"""
MinIO 客户端封装
"""
from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
import uuid
from datetime import timedelta
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_HOST,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE
        )
        self.default_bucket = "agent-files"
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保默认存储桶存在"""
        try:
            if not self.client.bucket_exists(self.default_bucket):
                self.client.make_bucket(self.default_bucket)
                logger.info(f"Created bucket: {self.default_bucket}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise
    
    def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        bucket_name: Optional[str] = None,
        object_name: Optional[str] = None
    ) -> dict:
        """
        上传文件到 MinIO
        
        Args:
            file_data: 文件二进制流
            filename: 原始文件名
            content_type: 文件类型
            bucket_name: 存储桶名称（可选）
            object_name: 对象名称（可选，默认自动生成）
        
        Returns:
            dict: 包含文件元数据的字典
        """
        bucket = bucket_name or self.default_bucket
        object_name = object_name or f"{uuid.uuid4()}-{filename}"
        
        try:
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            self.client.put_object(
                bucket,
                object_name,
                file_data,
                file_size,
                content_type=content_type
            )
            
            logger.info(f"Uploaded file: {object_name} to bucket: {bucket}")
            
            return {
                "bucket_name": bucket,
                "object_name": object_name,
                "filename": filename,
                "file_size": file_size,
                "content_type": content_type
            }
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def get_file_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        expires: int = 3600
    ) -> str:
        """
        获取文件临时访问URL
        
        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称（可选）
            expires: URL有效期（秒）
        
        Returns:
            str: 临时访问URL
        """
        bucket = bucket_name or self.default_bucket
        
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Error getting file URL: {e}")
            raise
    
    def delete_file(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> bool:
        """
        删除文件
        
        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称（可选）
        
        Returns:
            bool: 删除是否成功
        """
        bucket = bucket_name or self.default_bucket
        
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted file: {object_name} from bucket: {bucket}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise


minio_client = MinIOClient()