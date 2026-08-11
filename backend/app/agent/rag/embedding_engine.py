"""
RAG 向量化模块

实现文本向量化和 Qdrant 入库功能。
"""
import os
import logging
from typing import List, Dict, Any, Optional
import uuid

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny
)

from app.config import get_settings
from app.agent.rag.document_processor import DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingEngine:
    """
    向量化引擎
    
    使用 DashScope/OpenAI Embeddings 进行文本向量化。
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 100
    ):
        """
        初始化向量化引擎
        
        Args:
            model: Embedding 模型名称
            batch_size: 批量处理大小
        """
        self.model = model
        self.batch_size = batch_size
        
        # 优先使用 DashScope API（阿里向量模型）
        dashscope_api_key = settings.DASHSCOPE_API_KEY
        dashscope_base_url = settings.DASHSCOPE_BASE_URL
        dashscope_model = settings.DASHSCOPE_MODEL
        
        if dashscope_api_key and dashscope_base_url:
            # 使用 DashScope API（使用 OpenAI SDK）
            self.client = OpenAI(
                api_key=dashscope_api_key,
                base_url=dashscope_base_url
            )
            self.model = dashscope_model
            self.provider = "dashscope"
            logger.info(f"Initialized EmbeddingEngine with DashScope API, model: {dashscope_model}")
        else:
            # 尝试使用 OpenAI API
            openai_api_key = os.getenv('OPENAI_API_KEY', '')
            
            if openai_api_key:
                # 使用 OpenAI API
                self.client = OpenAI(api_key=openai_api_key)
                self.provider = "openai"
                logger.info(f"Initialized EmbeddingEngine with OpenAI API, model: {model}")
            else:
                # 没有可用的 Embedding API
                self.client = None
                self.provider = None
                logger.warning(
                    "No Embedding API configured. "
                    "Please configure DASHSCOPE_API_KEY or OPENAI_API_KEY in .env file."
                )
    
    def embed_text(self, text: str) -> List[float]:
        """
        向量化单个文本
        
        Args:
            text: 文本内容
        
        Returns:
            向量列表
        """
        if not self.client:
            raise ValueError(
                "Embedding engine not initialized. "
                "Please configure DASHSCOPE_API_KEY or OPENAI_API_KEY in .env file."
            )
        
        try:
            # DashScope API 要求 input 必须是字符串数组
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]  # 必须是数组
            )
            
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化文本
        
        Args:
            texts: 文本列表
        
        Returns:
            向量列表
        """
        if not self.client:
            raise ValueError(
                "Embedding engine not initialized. "
                "Please configure DASHSCOPE_API_KEY or OPENAI_API_KEY in .env file."
            )
        
        try:
            # 批量处理，每次最多处理 batch_size 个文本
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                # 按顺序提取向量
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise


class QdrantManager:
    """
    Qdrant 向量库管理器
    
    管理向量集合的创建、插入、查询等操作。
    """
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base",
        vector_size: Optional[int] = None
    ):
        """
        初始化 Qdrant 管理器
        
        Args:
            collection_name: 集合名称
            vector_size: 向量维度（None 表示自动检测）
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # 初始化 Qdrant 客户端（增加超时时间，避免创建集合超时）
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            timeout=30  # 超时时间 30 秒
        )
        
        # 如果没有指定向量维度，则延迟创建集合
        self._collection_created = False
        
        logger.info(f"Initialized QdrantManager for collection: {collection_name}")
    
    def _ensure_collection(self, vector_size: Optional[int] = None):
        """
        确保集合存在
        
        Args:
            vector_size: 向量维度
        """
        if vector_size:
            self.vector_size = vector_size
        
        if not self.vector_size:
            raise ValueError("Vector size must be specified")
        
        try:
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # 创建集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name} with vector size: {self.vector_size}")
            else:
                # 检查向量维度是否匹配
                collection_info = self.client.get_collection(self.collection_name)
                actual_size = collection_info.config.params.vectors.size
                
                if actual_size != self.vector_size:
                    logger.warning(
                        f"Collection {self.collection_name} has vector size {actual_size}, "
                        f"but expected {self.vector_size}. "
                        f"Please delete and recreate the collection."
                    )
            
            self._collection_created = True
            
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise
    
    def insert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> int:
        """
        插入文档切片
        
        Args:
            chunks: 文档切片列表
            embeddings: 向量列表
        
        Returns:
            插入的点数量
        """
        try:
            # 确保集合存在（使用第一个向量的维度）
            if not self._collection_created and embeddings:
                self._ensure_collection(len(embeddings[0]))
            
            # 创建点结构
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "chunk_id": chunk.chunk_id
                    }
                )
                points.append(point)
            
            # 批量插入
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Inserted {len(points)} points into {self.collection_name}")
            
            return len(points)
            
        except Exception as e:
            logger.error(f"Failed to insert chunks: {e}")
            raise
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filter_conditions: 过滤条件
        
        Returns:
            搜索结果列表
        """
        try:
            # 构建过滤条件
            query_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    # 处理 $in 操作符（列表匹配）
                    if isinstance(value, dict) and "$in" in value:
                        conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchAny(any=value["$in"])
                            )
                        )
                    else:
                        # 单值匹配
                        conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=value)
                            )
                        )
                query_filter = Filter(must=conditions)
            
            # 执行搜索（使用 query_points 方法）
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # 格式化结果
            formatted_results = []
            for result in results.points:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload["content"],
                    "metadata": result.payload["metadata"],
                    "chunk_id": result.payload["chunk_id"]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            raise
    
    def delete_by_metadata(self, metadata_key: str, metadata_value: Any) -> int:
        """
        根据元数据删除点
        
        Args:
            metadata_key: 元数据键
            metadata_value: 元数据值
        
        Returns:
            删除的点数量
        """
        try:
            # 构建过滤条件
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key=f"metadata.{metadata_key}",
                        match=MatchValue(value=metadata_value)
                    )
                ]
            )
            
            # 删除点
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=query_filter
            )
            
            logger.info(f"Deleted points with {metadata_key}={metadata_value}")
            
            return 1
            
        except Exception as e:
            logger.error(f"Failed to delete by metadata: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "points_count": info.points_count,
                "status": info.status.value
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise


class RAGIndexer:
    """
    RAG 索引器
    
    完整的文档索引流程：向量化 → 入库。
    """
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base"
    ):
        """
        初始化 RAG 索引器
        
        Args:
            collection_name: 集合名称
        """
        self.embedding_engine = EmbeddingEngine()
        self.qdrant_manager = QdrantManager(collection_name)
    
    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        索引文档切片
        
        Args:
            chunks: 文档切片列表
        
        Returns:
            索引的切片数量
        """
        try:
            # 批量向量化
            texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_engine.embed_batch(texts)
            
            # 插入 Qdrant
            count = self.qdrant_manager.insert_chunks(chunks, embeddings)
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to index chunks: {e}")
            raise
    
    def search_similar(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似内容
        
        Args:
            query: 查询文本
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filter_conditions: 过滤条件
        
        Returns:
            搜索结果列表
        """
        try:
            # 向量化查询
            query_vector = self.embedding_engine.embed_text(query)
            
            # 搜索
            results = self.qdrant_manager.search(
                query_vector,
                limit,
                score_threshold,
                filter_conditions
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar: {e}")
            raise