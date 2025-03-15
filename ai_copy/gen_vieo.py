from moviepy.editor import ImageClip,CompositeVideoClip,AudioFileClip,TextClip,concatenate_videoclips,VideoFileClip
from utils import *
import os
import tempfile
import requests
import random
import string
import mimetypes
from typing import List


def get_file_extension_from_content(response: requests.Response) -> str:
    """根据 Content-Type 确定文件扩展名"""
    content_type = response.headers.get("Content-Type", "")
    extension = mimetypes.guess_extension(content_type)
    return extension if extension else ".mp4"  # 默认使用 .mp4


def generate_random_filename(extension: str) -> str:
    """生成随机文件名"""
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    return f"{random_str}{extension}"


def generate_unique_path(extension: str) -> str:
    """生成唯一的文件路径"""
    unique_folder = os.path.join(tempfile.gettempdir(),
                                 ''.join(random.choices(string.ascii_letters + string.digits, k=15)))
    os.makedirs(unique_folder, exist_ok=True)
    return os.path.join(unique_folder, generate_random_filename(extension))


def download_video(video_url: str) -> str:
    """下载视频并返回唯一的本地路径"""
    response = requests.get(video_url, stream=True)
    response.raise_for_status()

    file_extension = get_file_extension_from_content(response)
    video_path = generate_unique_path(file_extension)

    with open(video_path, "wb") as video_file:
        for chunk in response.iter_content(chunk_size=8192):
            video_file.write(chunk)

    return video_path


def get_key_images(video_url: str) -> List[str]:
    """输入视频 URL，返回关键帧图片的 URL 列表"""
    try:
        # 1. 下载视频
        video_path = download_video(video_url)

        # 2. 提取关键帧
        video_folder_path = get_key_frames(video_path)

        # 3. 遍历关键帧并上传
        image_urls = []
        for img_name in sorted(os.listdir(video_folder_path)):
            img_path = os.path.join(video_folder_path, img_name)
            img_url = upload_file(img_path)
            image_urls.append(img_url)

        return image_urls
    finally:
        # 4. 清理临时文件
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(video_folder_path):
            for img_name in os.listdir(video_folder_path):
                os.remove(os.path.join(video_folder_path, img_name))
            os.rmdir(video_folder_path)


def gen_key_video(prompt,time_len,resolution,movement_amplitude,aspect_ratio,image_urls):
    """根据关键帧和替换图片生成一个视频片段
        image_urls: 第一个是关键帧,第二个是替换图片
        这里返回一个taskid,前端轮询请求
    """
    rsp = send_video_generation_request(prompt, image_urls, time_len, resolution, movement_amplitude, aspect_ratio)
    task_id = rsp['task_id']
    return task_id

def get_task_id(task_id):
    """根据task_id获取生成视频片段的url"""
    check_res = check_video_gen_status(task_id)
    video_url = ''
    if len(check_res):
        if 'url' in check_res[0]:
            video_url = check_res[0]['url']
    return video_url

def merge_videos(video_urls, product_info):
    """合并视频,返回一个视频url
    video_urls: 视频链接url列表
    """
    # 1.先下载所有视频片段到本地,假设下载后存储在本地tmp_videos文件夹下
    video_paths = []
    for video_url in video_urls:
        video_paths.append(download_video(video_url))

    video_clips = []
    for video_path in video_paths:
        video_clip = VideoFileClip(video_path)
        video_clips.append(video_clip)
    final_clip = concatenate_videoclips(video_clips)

    # 获取bgm
    audio_names=os.listdir('tmp_audios')
    audio_path_list=[os.path.join('tmp_audios',audio_name) for audio_name in audio_names]
    audio_clip=AudioFileClip(random.choice(audio_path_list))

    # 处理音频和视频时长不一致的情况
    video_duration = final_clip.duration
    audio_duration = audio_clip.duration
    if audio_duration > video_duration:
        # 音频时长大于视频时长：截断音频
        audio_clip = audio_clip.subclip(0, video_duration)
    elif audio_duration < video_duration:
        # 音频时长小于视频时长：复制音频
        audio_clips = []
        while audio_duration < video_duration:
            audio_clips.append(audio_clip)
            audio_duration += audio_clip.duration
        # 如果复制后的音频总时长仍然小于视频时长，再复制一次
        if audio_duration < video_duration:
            audio_clips.append(audio_clip.subclip(0, video_duration - audio_duration))
    final_clip=final_clip.set_audio(audio_clip)

    # 保存最终的视频
    final_video_path = generate_unique_path(".mp4")
    final_clip.write_videofile(final_video_path, codec="libx264", fps=24)
    # 上传到文件服务器
    video_url = upload_file(final_video_path)
    titles = get_video_title(product_info, final_video_path)
    return {'video_url': video_url, 'titles': titles}

def upload_file(file_path):
    # 接口URL
    url = "http://localhost:5000/api/upload/file"

    # 读取文件并上传
    with open(file_path, "rb") as file:
        files = {"file": (file_path, file, "image/jpeg")}
        response = requests.post(url, files=files)

    # 打印服务器返回的响应
    print(response.json())
    return response.json()['preview_url']

def get_video_title(product_info, video_path):
    frame_folder_path = get_key_frames(video_path)
    # 展示关键帧
    scene_images = os.listdir(frame_folder_path)
    scene_images.sort()
    image_paths = [os.path.join(frame_folder_path, frame_name) for frame_name in scene_images]
    # 结合用户输入的产品信息，组织prompt
    prompt_tmp = open("prompts/prompt_title_generation.txt").read()
    prompt = prompt_tmp.replace('aaaaa', product_info)

    # 调用gpt，产生标题信息
    raw_title_res = call_multi_model_gpt(prompt, image_paths, image_mode='local_path')
    title_res = parse_json_response(raw_title_res)
    return title_res['广告标题']


