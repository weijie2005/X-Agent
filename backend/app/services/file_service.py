"""
文件服务层
"""
from sqlalchemy.orm import Session
from typing import Optional, BinaryIO
from uuid import UUID
import logging

from app.models.tables import FileMetadata, Session
from app.utils.minio_client import minio_client

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.minio = minio_client
    
    def upload_file(
        self,
        session_id: UUID,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None
    ) -> FileMetadata:
        """
        上传文件到 MinIO 并记录元数据
        
        Args:
            session_id: 会话ID
            file_data: 文件二进制流
            filename: 文件名
            content_type: 文件类型
        
        Returns:
            FileMetadata: 文件元数据对象
        """
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        upload_result = self.minio.upload_file(
            file_data=file_data,
            filename=filename,
            content_type=content_type
        )
        
        file_metadata = FileMetadata(
            session_id=session_id,
            filename=filename,
            object_name=upload_result["object_name"],
            bucket_name=upload_result["bucket_name"],
            file_size=upload_result["file_size"],
            content_type=content_type
        )
        
        self.db.add(file_metadata)
        self.db.commit()
        self.db.refresh(file_metadata)
        
        logger.info(f"Uploaded file {filename} for session {session_id}")
        return file_metadata
    
    def get_file(self, file_id: UUID) -> Optional[FileMetadata]:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
        
        Returns:
            FileMetadata: 文件元数据对象
        """
        return self.db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
    
    def get_session_files(self, session_id: UUID) -> list[FileMetadata]:
        """
        获取会话的所有文件
        
        Args:
            session_id: 会话ID
        
        Returns:
            list[FileMetadata]: 文件列表
        """
        return self.db.query(FileMetadata).filter(
            FileMetadata.session_id == session_id
        ).all()
    
    def get_file_url(self, file_id: UUID, expires: int = 3600) -> Optional[str]:
        """
        获取文件临时访问URL
        
        Args:
            file_id: 文件ID
            expires: URL有效期（秒）
        
        Returns:
            str: 临时访问URL
        """
        file_metadata = self.get_file(file_id)
        if not file_metadata:
            return None
        
        return self.minio.get_file_url(
            object_name=file_metadata.object_name,
            bucket_name=file_metadata.bucket_name,
            expires=expires
        )
    
    def delete_file(self, file_id: UUID) -> bool:
        """
        删除文件（MinIO + 数据库）
        
        Args:
            file_id: 文件ID
        
        Returns:
            bool: 删除是否成功
        """
        file_metadata = self.get_file(file_id)
        if not file_metadata:
            return False
        
        try:
            self.minio.delete_file(
                object_name=file_metadata.object_name,
                bucket_name=file_metadata.bucket_name
            )
            
            self.db.delete(file_metadata)
            self.db.commit()
            
            logger.info(f"Deleted file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            self.db.rollback()
            raise