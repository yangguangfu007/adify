import os
import time
from flask import jsonify
from minio import Minio
from werkzeug.utils import secure_filename
from mimetypes import guess_type
from datetime import timedelta

class MinioUploader:
    def __init__(self, bucket_name):
        """
        初始化Minio客户端和存储桶
        :param bucket_name: 存储桶名称
        """
        self.minio_client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT"),  # MinIO服务器地址
            access_key=os.getenv("MINIO_ACCESS_KEY"),  # Access Key
            secret_key=os.getenv("MINIO_SECRET_KEY"),  # Secret Key
            secure=os.getenv("MINIO_SECURE") == "True"  # 如果使用HTTPS，设置为True
        )
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """
        确保存储桶存在
        """
        if not self.minio_client.bucket_exists(self.bucket_name):
            self.minio_client.make_bucket(self.bucket_name)
            print(f"Bucket '{self.bucket_name}' created.")
        else:
            print(f"Bucket '{self.bucket_name}' already exists.")

    def upload_file(self, file):
        """
        上传文件到MinIO并生成Presigned URL
        :param file: 上传的文件对象
        :return: JSON响应
        """
        # 保存文件到MinIO
        timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        filename = timestamp + '-' + secure_filename(file.filename)
        file_path = os.path.join("/tmp", filename)  # 临时保存文件
        file.save(file_path)

        # 获取文件的MIME类型
        content_type, _ = guess_type(file.filename)
        if not content_type:
            content_type = "application/octet-stream"  # 默认类型
        print(f"获取到的content_type: {content_type}")

        try:
            # 上传到MinIO
            self.minio_client.fput_object(self.bucket_name, filename, file_path, content_type=content_type)

            # 生成Presigned URL
            expires = timedelta(days=7)
            presigned_url = self.minio_client.presigned_get_object(self.bucket_name, filename, expires=expires)
            print(f"Presigned URL for {filename}: {presigned_url}")
            minio_url = os.getenv("MINIO_ENDPOINT_PROXY") + "/" + self.bucket_name + "/" + filename
            return jsonify({"message": "File uploaded successfully", "url": minio_url, "preview_url": presigned_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            os.remove(file_path)  # 删除临时文件