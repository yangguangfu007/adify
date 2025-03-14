"""
API module for the adify service.
Contains route definitions for the API endpoints.
"""
import os
from flask import Blueprint, jsonify, request
from db.db import DBManager
from upload.uploadfile import MinioUploader
from datetime import datetime
import uuid
import traceback

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize database manager
db_manager = DBManager(host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT")), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
                       database=os.getenv("DB_DATABASE"))
minioUploader = MinioUploader(os.getenv("BUCKET_NAME"))


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Service is running'}), 200


@api_bp.route('/video/keyframes', methods=['POST'])
def keyframes():
    """该接口用于接收一个视频的URL，提取视频中的关键帧，并以图片格式返回多个关键帧。关键帧提取基于视频内容的显著变化，可用于视频分析、内容摘要或视频检索等场景。"""
    try:
        data = request.get_json()
        if not data or not data.get('video_url'):
            return jsonify({'status': 'error', 'message': '视频url为空'}), 400
        # todo
        keyframes = []
        return jsonify({'status': 'success', 'message': 'ok', 'keyframes': keyframes}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/video/generate_video_segments', methods=['POST'])
def generate_video_segments():
    """该接口用于接收一个视频的URL和多个关键帧替换图片的URL，根据关键帧位置将视频分割为多个片段，并将每个关键帧替换为指定的图片。
    每个关键帧替换图片的URL对应一组视频片段，每组包含3个片段。该接口可用于视频编辑、广告替换或内容定制等场景。
    """
    try:
        data = request.get_json()
        if not data or not data.get('video_url') or not data.get('keyframes'):
            return jsonify({'status': 'error', 'message': '视频url或keyframes为空'}), 400
        results = []
        # TODO
        return jsonify({'status': 'success', 'message': 'ok', 'results': results}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/video/generate_video', methods=['POST'])
def generate_video():
    """视频生成和标题推荐接口"""
    try:
        data = request.get_json()
        if not data or not data.get('video_fragments'):
            return jsonify({'status': 'error', 'message': 'video_fragments is null'}), 400

        video = {}
        titles = []
        return jsonify({'status': 'success', 'message': 'ok', 'video': video, 'titles': titles}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/video/add', methods=['POST'])
def video_add():
    """添加视频素材(站内或站外)接口"""
    try:
        data = request.get_json()
        print('data:', data)
        if not data or not data.get('video_url') or not data.get('preview_url') or not data.get('title'):
            return jsonify({'status': 'error', 'message': 'video_url or preview_url or title or type is null'}), 400

        # 提取请求中的数据
        video_url = data['video_url']
        preview_url = data['preview_url']
        title = data['title']
        source_type = data['type']  # type 是 0（站内）或 1（站外）

        # 构造插入语句
        insert_query = """
                INSERT INTO video_materials (material_id, video_url, preview_url, title, source_type)
                VALUES (%s, %s, %s, %s, %s)
            """
        material_id = generate_material_id(source_type)
        # 插入数据
        params = (material_id, video_url, preview_url, title, source_type)

        result = db_manager.execute_insert(insert_query, params)
        if result != 0:  # 如果插入成功
            return jsonify(
                {'status': 'success', 'message': 'Video uploaded successfully', 'material_id': material_id}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to upload video'}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/video/update', methods=['POST'])
def video_update():
    """视频素材更新接口"""
    try:
        data = request.get_json()
        print('data:', data)
        if not data or not data.get('material_id') or not data.get('deployment_links'):
            return jsonify({'status': 'error', 'message': 'video_url or preview_url or title or type is null'}), 400

        # 提取请求中的数据
        material_id = data['material_id']
        deployment_links = data['deployment_links']

        # 构造更新语句
        update_query = """
                UPDATE video_materials
                SET campaign_urls = %s
                WHERE material_id = %s
            """

        params = (deployment_links, material_id)
        result = db_manager.execute(update_query, params)
        if result != 0:  # 如果更新成功
            return jsonify(
                {'status': 'success', 'message': 'Video update successfully', 'material_id': material_id}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to upload video'}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


def generate_material_id(source_type=0):
    """生成素材 ID"""
    # 获取当前日期
    today = datetime.now().strftime('%Y%m%d')
    if source_type == 0:
        prefix = f"C{today}"
    else:
        prefix = f"CW{today}"

    # 查询当天的最大顺序号
    query = """
        SELECT MAX(CAST(SUBSTRING(material_id, -3) AS UNSIGNED)) AS max_sequence
        FROM video_materials
        WHERE material_id LIKE %s
    """
    params = (f"{prefix}%",)
    result = db_manager.fetch_one(query, params)

    # 如果没有记录，则从 001 开始
    max_sequence = result['max_sequence'] if result and result['max_sequence'] else 0
    new_sequence = max_sequence + 1

    # 生成素材 ID
    material_id = f"{prefix}{new_sequence:03d}"  # 顺序号至少3位，不足补零
    return material_id

@api_bp.route('/video/list', methods=['GET'])
def video_list():
    """视频素材列表查询接口"""
    # 获取查询参数
    page = request.args.get('page', default=1, type=int)
    size = request.args.get('size', default=10, type=int)
    search = request.args.get('search', default='', type=str)
    # 计算分页查询的偏移量
    offset = (page - 1) * size

    # 构造查询语句
    base_query = """
            SELECT 
                id, 
                material_id, 
                title, 
                campaign_urls as deployment_links,
                created_at
            FROM 
                video_materials
            WHERE 
                1=1
        """
    # 添加搜索条件（如果提供了搜索关键词）
    if search:
        base_query += " AND (material_id LIKE %s OR title LIKE %s)"
        search_condition = (f"%{search}%", f"%{search}%")
    else:
        search_condition = ()

    # 分页查询
    query = base_query + " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params = search_condition + (size, offset)

    # 查询总记录数
    total_query = """
                SELECT 
                    count(id) as totalCount
                FROM 
                    video_materials
            """

    try:
        # 执行分页查询
        results = db_manager.fetch_all(query, params)
        if results is None:
            return jsonify({'status': 'error', 'message': 'No data found'}), 400

        # 获取总记录数
        total = db_manager.fetch_one(total_query)['totalCount']

        # 构造响应数据
        videos = []
        for row in results:
            videos.append({
                "material_id": row['material_id'],
                "title": row['title'],
                "deployment_links": row['deployment_links'],
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M:%S') # 转换为 YYYY-mm-dd HH:MM:SS 格式
            })

        response_data = {
            "total": total,
            "page": page,
            "size": size,
            "videos": videos
        }

        return jsonify(
            {'status': 'success', 'message': 'Video list retrieved successfully', 'data': response_data}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve video list: {str(e)}'}), 500


@api_bp.route('/deployment/add', methods=['POST'])
def deployment_add():
    """投放对比组生成接口"""
    try:
        data = request.get_json()
        if not data or not data.get('materials'):
            return jsonify({'status': 'error', 'message': 'materials is null'}), 400

        # 生成唯一的对比组 ID
        comparison_group_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

        # 准备批量插入的数据列表
        insert_data = []

        # 根据素材id列表，查询所有素材信息
        material_ids = data.get('materials')
        query = """
            SELECT material_id, campaign_urls
            FROM video_materials 
            WHERE material_id IN %s
        """
        results = db_manager.fetch_all(query, (tuple(material_ids),))

        # 构建素材ID到投放链接的映射
        for row in results:
            material_id = row['material_id']
            campaign_urls = row['campaign_urls']
            result_list = campaign_urls.split(',')
            for link in result_list:
                # 设置默认值
                campaign_label = 'Default Label'
                is_system_preferred = False

                # 构造一条插入记录
                insert_data.append((
                    comparison_group_id, material_id, link, campaign_label,is_system_preferred
                ))

        # 执行批量插入
        if insert_data:
            insert_query = """
                   INSERT INTO material_comparison_groups (
                       comparison_group_id, material_id, campaign_url, campaign_label,is_system_preferred
                   ) VALUES (%s, %s, %s, %s, %s)
               """
            db_manager.batch_execute_insert(insert_query, insert_data)

        return jsonify({'status': 'success', 'message': 'Deployment group created successfully',
                        'group_id': comparison_group_id}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/deployment/list', methods=['GET'])
def deployment_list():
    """查询投放对比组列表(分页) """
    # 获取查询参数
    page = request.args.get('page', default=1, type=int)
    size = request.args.get('size', default=10, type=int)
    # 计算分页查询的偏移量
    offset = (page - 1) * size

    # 查询数据库获取投放对比组列表
    query = """
            SELECT 
                comparison_group_id,
                GROUP_CONCAT(material_id) AS material_ids
            FROM 
                material_comparison_groups
            GROUP BY 
                comparison_group_id
            ORDER BY 
                MAX(created_at) DESC
            LIMIT %s OFFSET %s
        """
    params = (size, offset)

    # 查询总记录数
    total_query = """
            SELECT 
                COUNT(DISTINCT comparison_group_id) AS total
            FROM 
                material_comparison_groups
        """
    try:
        # 执行分页查询
        results = db_manager.fetch_all(query, params)
        if results is None:
            return jsonify({'status': 'error', 'message': 'No data found'}), 404

        # 获取总记录数
        total = db_manager.fetch_one(total_query)['total']

        # 构造响应数据
        groups = []
        for row in results:
            groups.append({
                "group_id": row['comparison_group_id'],
                "material_ids": row['material_ids'].split(',') if row['material_ids'] else []
            })

        response_data = {
            "total": total,
            "page": page,
            "size": size,
            "groups": groups
        }

        return jsonify({'status': 'success', 'message': 'Deployment group list retrieved successfully',
                        'data': response_data}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve deployment group list: {str(e)}'}), 500


@api_bp.route('/deployment/details', methods=['GET'])
def deployment_details():
    """根据对比组ID查询素材列表详情接口 """
    # 获取查询参数
    group_id = request.args.get('group_id', default='', type=str)
    print('group_id', group_id)
    if not group_id:
        return jsonify({'status': 'error', 'message': 'Group ID is required'}), 400

        # 查询数据库获取素材详情
    query = """
            SELECT 
                m.material_id, 
                m.preview_url as video_url, 
                mc.campaign_url AS deployment_url,
                mc.click_count AS clicks,
                mc.completion_count AS completes,
                mc.like_count AS likes,
                mc.comment_count AS comments,
                mc.share_count AS shares,
                mc.is_system_preferred AS is_preferred
            FROM 
                video_materials m
            JOIN 
                material_comparison_groups mc ON m.material_id = mc.material_id
            WHERE 
                mc.comparison_group_id = %s
        """
    params = (group_id,)

    try:
        # 执行查询并获取结果
        results = db_manager.fetch_all(query, params)
        if results is None:
            return jsonify({'status': 'error', 'message': 'No data found for the given group ID'}), 400

        # 构造响应数据
        materials = []
        for row in results:
            material = {
                "material_id": row['material_id'],
                "video_url": row['video_url'],
                "deployment_url": row['deployment_url'],
                "clicks": row['clicks'],
                "completes": row['completes'],
                "likes": row['likes'],
                "comments": row['comments'],
                "shares": row['shares'],
                "is_preferred": row['is_preferred']
            }
            materials.append(material)

        response_data = {
            "group_id": group_id,
            "materials": materials
        }

        return jsonify(
            {'status': 'success', 'message': 'Material details retrieved successfully', 'data': response_data}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve material details: {str(e)}'}), 500



@api_bp.route('/deployment/data', methods=['POST'])
def deployment_data():
    """投放数据抓取接口(爬虫接口)"""
    try:
        data = request.get_json()
        if not data or not data.get('material_id') or not data.get('deployment_url'):
            return jsonify({'status': 'error', 'message': 'material_id or deployment_url is null'}), 400
        result = []
        return jsonify({'status': 'success', 'message': 'Deployment data retrieved successfully', 'data': result}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/upload/file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    return minioUploader.upload_file(file)
