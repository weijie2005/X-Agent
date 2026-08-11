"""
知识库服务层

提供知识库管理、文档上传、文档索引等功能
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging
import os
import tempfile
import uuid

from app.models.tables import KnowledgeBase, Document
from app.models.schemas import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.agent.rag.document_processor import DocumentProcessor
from app.agent.rag.embedding_engine import RAGIndexer

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """知识库服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.document_processor = DocumentProcessor()
    
    def create_knowledge_base(
        self,
        kb_data: KnowledgeBaseCreate,
        user_id: Optional[UUID] = None
    ) -> KnowledgeBase:
        """
        创建知识库
        
        Args:
            kb_data: 知识库创建数据
            user_id: 用户ID
        
        Returns:
            KnowledgeBase: 创建的知识库对象
        """
        # 生成集合名称
        collection_name = kb_data.collection_name or f"kb_{uuid.uuid4().hex[:12]}"
        
        # 创建知识库记录
        kb = KnowledgeBase(
            name=kb_data.name,
            description=kb_data.description,
            collection_name=collection_name,
            user_id=user_id
        )
        
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        
        # 创建Qdrant集合
        try:
            indexer = RAGIndexer(collection_name)
            indexer.create_collection()
            logger.info(f"Created Qdrant collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")
        
        logger.info(f"Created knowledge base: {kb.id}")
        return kb
    
    def get_knowledge_base(self, kb_id: UUID) -> Optional[KnowledgeBase]:
        """
        获取知识库详情
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            KnowledgeBase: 知识库对象
        """
        return self.db.query(KnowledgeBase).filter(
            and_(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.is_active == True
            )
        ).first()
    
    def list_knowledge_bases(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[KnowledgeBase]:
        """
        获取知识库列表
        
        Args:
            user_id: 用户ID（可选）
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        query = self.db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
        
        if user_id:
            query = query.filter(KnowledgeBase.user_id == user_id)
        
        return query.order_by(KnowledgeBase.updated_at.desc()).offset(skip).limit(limit).all()
    
    def update_knowledge_base(
        self,
        kb_id: UUID,
        kb_data: KnowledgeBaseUpdate
    ) -> Optional[KnowledgeBase]:
        """
        更新知识库
        
        Args:
            kb_id: 知识库ID
            kb_data: 更新数据
        
        Returns:
            KnowledgeBase: 更新后的知识库对象
        """
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return None
        
        if kb_data.name is not None:
            kb.name = kb_data.name
        if kb_data.description is not None:
            kb.description = kb_data.description
        if kb_data.is_active is not None:
            kb.is_active = kb_data.is_active
        
        self.db.commit()
        self.db.refresh(kb)
        
        logger.info(f"Updated knowledge base: {kb_id}")
        return kb
    
    def delete_knowledge_base(self, kb_id: UUID) -> bool:
        """
        删除知识库（软删除）
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            bool: 删除是否成功
        """
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False
        
        kb.is_active = False
        self.db.commit()
        
        # 删除Qdrant集合
        try:
            indexer = RAGIndexer(kb.collection_name)
            indexer.delete_collection()
            logger.info(f"Deleted Qdrant collection: {kb.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete Qdrant collection: {e}")
        
        logger.info(f"Deleted knowledge base: {kb_id}")
        return True
    
    async def upload_document(
        self,
        kb_id: UUID,
        file_content: bytes,
        filename: str,
        file_type: str
    ) -> Document:
        """
        上传文档到知识库
        
        Args:
            kb_id: 知识库ID
            file_content: 文件内容
            filename: 文件名
            file_type: 文件类型
        
        Returns:
            Document: 创建的文档对象
        """
        # 检查知识库是否存在
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")
        
        # 创建文档记录
        document = Document(
            kb_id=kb_id,
            filename=filename,
            file_type=file_type,
            file_size=len(file_content),
            is_indexed=False
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # 异步索引文档
        try:
            await self._index_document(document, file_content, kb.collection_name)
        except Exception as e:
            logger.error(f"Failed to index document {document.id}: {e}")
            document.indexing_error = str(e)
            self.db.commit()
        
        return document
    
    async def _index_document(
        self,
        document: Document,
        file_content: bytes,
        collection_name: str
    ):
        """
        索引文档
        
        Args:
            document: 文档对象
            file_content: 文件内容
            collection_name: 集合名称
        """
        logger.info(f"Indexing document: {document.id}")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{document.file_type}") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理文档
            chunks = self.document_processor.process_document(
                tmp_file_path,
                metadata={
                    "document_id": str(document.id),
                    "filename": document.filename,
                    "file_type": document.file_type
                }
            )
            
            # 向量化并存储
            indexer = RAGIndexer(collection_name)
            indexer.index_chunks(chunks)
            
            # 更新文档状态
            document.chunk_count = len(chunks)
            document.is_indexed = True
            document.indexing_error = None
            self.db.commit()
            
            logger.info(f"Indexed {len(chunks)} chunks for document {document.id}")
            
        finally:
            # 删除临时文件
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    def list_documents(
        self,
        kb_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Document]:
        """
        获取知识库文档列表
        
        Args:
            kb_id: 知识库ID
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            List[Document]: 文档列表
        """
        return self.db.query(Document).filter(
            Document.kb_id == kb_id
        ).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    def delete_document(self, kb_id: UUID, document_id: UUID) -> bool:
        """
        删除文档
        
        Args:
            kb_id: 知识库ID
            document_id: 文档ID
        
        Returns:
            bool: 删除是否成功
        """
        document = self.db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.kb_id == kb_id
            )
        ).first()
        
        if not document:
            return False
        
        # 删除向量数据
        try:
            kb = self.get_knowledge_base(kb_id)
            if kb:
                indexer = RAGIndexer(kb.collection_name)
                indexer.delete_by_metadata({"document_id": str(document_id)})
                logger.info(f"Deleted vectors for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
        
        # 删除数据库记录
        self.db.delete(document)
        self.db.commit()
        
        logger.info(f"Deleted document: {document_id}")
        return True