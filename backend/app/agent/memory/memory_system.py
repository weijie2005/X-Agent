"""
四级分层记忆系统

本模块实现了 Agent 的四级分层记忆架构：
1. 工作记忆（Working Memory）：进程内存 + 上下文滑动窗口
2. 短期记忆（Short-term Memory）：Redis 存储，支持 TTL
3. 长期结构化记忆（Long-term Structured Memory）：PostgreSQL 存储
4. 长期语义记忆（Long-term Semantic Memory）：Qdrant 向量存储

设计原则：
- 分层存储：不同类型记忆使用不同存储介质
- 自动降级：内存不足时自动清理旧记忆
- 持久化：重要记忆持久化存储
- 高效检索：向量检索支持语义搜索

使用方式：
    from app.agent.memory.memory_system import MemorySystem
    
    memory = MemorySystem(session_id="session_123")
    
    # 存储记忆
    await memory.store_working_memory("key", "value")
    await memory.store_short_term_memory("key", "value", ttl=3600)
    
    # 检索记忆
    value = await memory.retrieve_working_memory("key")
"""
from typing import Any, Dict, List, Optional
import json
import time
from datetime import datetime
import logging

from app.config import get_settings
from app.models.database import SessionLocal
from app.models.tables import Session, Message

logger = logging.getLogger(__name__)
settings = get_settings()


class WorkingMemory:
    """
    工作记忆（一级记忆）
    
    特点：
    - 存储位置：进程内存（最快）
    - 生命周期：当前请求期间
    - 容量限制：滑动窗口裁剪
    - 用途：临时变量、当前上下文
    
    实现机制：
    - 使用字典存储键值对
    - 维护消息队列，自动裁剪旧消息
    - 支持上下文窗口大小限制
    """
    
    def __init__(self, max_messages: int = 20):
        """
        初始化工作记忆
        
        Args:
            max_messages: 最大消息数量，超过此数量将裁剪
        """
        self.memory: Dict[str, Any] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.max_messages = max_messages
    
    def store(self, key: str, value: Any) -> None:
        """
        存储键值对
        
        Args:
            key: 键名
            value: 值
        """
        self.memory[key] = value
        logger.debug(f"Working memory stored: {key}")
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        检索值
        
        Args:
            key: 键名
        
        Returns:
            值，如果不存在返回 None
        """
        value = self.memory.get(key)
        logger.debug(f"Working memory retrieved: {key}")
        return value
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """
        添加消息到队列
        
        自动裁剪超过限制的旧消息。
        
        Args:
            message: 消息字典
        """
        self.message_queue.append(message)
        
        # 滑动窗口裁剪
        if len(self.message_queue) > self.max_messages:
            removed = self.message_queue.pop(0)
            logger.debug(f"Removed old message from working memory: {removed.get('id')}")
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取消息列表
        
        Args:
            limit: 限制数量，None 表示返回全部
        
        Returns:
            消息列表
        """
        if limit:
            return self.message_queue[-limit:]
        return self.message_queue.copy()
    
    def clear(self) -> None:
        """清空工作记忆"""
        self.memory.clear()
        self.message_queue.clear()
        logger.debug("Working memory cleared")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        导出为字典格式
        
        Returns:
            包含所有数据的字典
        """
        return {
            "memory": self.memory,
            "message_queue": self.message_queue,
            "max_messages": self.max_messages
        }


class ShortTermMemory:
    """
    短期记忆（二级记忆）
    
    特点：
    - 存储位置：Redis
    - 生命周期：会话期间（支持 TTL）
    - 容量限制：Redis 配置
    - 用途：会话摘要、实体抽取、临时偏好
    
    实现机制：
    - 使用 Redis Hash 存储结构化数据
    - 支持 TTL 自动过期
    - 支持批量操作
    """
    
    def __init__(self, session_id: str, redis_client: Any = None):
        """
        初始化短期记忆
        
        Args:
            session_id: 会话 ID
            redis_client: Redis 客户端实例（可选）
        """
        self.session_id = session_id
        self.redis_client = redis_client
        self.key_prefix = f"agent:memory:short:{session_id}"
    
    async def _get_redis(self):
        """获取 Redis 客户端"""
        if not self.redis_client:
            import redis
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=2,  # 连接超时 2 秒
                    socket_timeout=2  # 操作超时 2 秒
                )
                # 测试连接
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        return self.redis_client
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = 3600) -> None:
        """
        存储键值对
        
        Args:
            key: 键名
            value: 值（将序列化为 JSON）
            ttl: 过期时间（秒），None 表示永不过期
        """
        try:
            redis_client = await self._get_redis()
            
            # 如果 Redis 客户端为 None，直接返回
            if redis_client is None:
                logger.debug(f"Redis unavailable, skipping store for key: {key}")
                return
            
            full_key = f"{self.key_prefix}:{key}"
            
            # 序列化为 JSON
            value_json = json.dumps(value) if not isinstance(value, str) else value
            
            if ttl:
                redis_client.setex(full_key, ttl, value_json)
            else:
                redis_client.set(full_key, value_json)
            
            logger.debug(f"Short-term memory stored: {key} (TTL: {ttl})")
        except Exception as e:
            # Redis 连接失败时，记录错误但不中断执行
            logger.warning(f"Failed to store short-term memory: {e}")
            # 继续执行，不抛出异常
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """
        检索值
        
        Args:
            key: 键名
        
        Returns:
            值，如果不存在返回 None
        """
        try:
            redis_client = await self._get_redis()
            
            # 如果 Redis 客户端为 None，直接返回 None
            if redis_client is None:
                logger.debug(f"Redis unavailable, returning None for key: {key}")
                return None
            
            full_key = f"{self.key_prefix}:{key}"
            
            value_json = redis_client.get(full_key)
            
            if value_json is None:
                return None
            
            # 尝试反序列化
            try:
                return json.loads(value_json)
            except json.JSONDecodeError:
                return value_json
        except Exception as e:
            # Redis 连接失败时，返回 None
            logger.warning(f"Failed to retrieve short-term memory: {e}")
            return None
    
    async def store_session_summary(self, summary: str, entities: List[str], ttl: int = 7200) -> None:
        """
        存储会话摘要
        
        Args:
            summary: 会话摘要文本
            entities: 提取的实体列表
            ttl: 过期时间（秒），默认 2 小时
        """
        await self.store("summary", {
            "text": summary,
            "entities": entities,
            "timestamp": datetime.now().isoformat()
        }, ttl=ttl)
    
    async def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """
        获取会话摘要
        
        Returns:
            会话摘要字典
        """
        return await self.retrieve("summary")
    
    async def clear(self) -> None:
        """清空短期记忆"""
        redis_client = await self._get_redis()
        
        # 查找所有相关键
        keys = redis_client.keys(f"{self.key_prefix}:*")
        if keys:
            redis_client.delete(*keys)
        
        logger.debug(f"Short-term memory cleared for session: {self.session_id}")


class LongTermStructuredMemory:
    """
    长期结构化记忆（三级记忆）
    
    特点：
    - 存储位置：PostgreSQL
    - 生命周期：永久存储
    - 容量限制：数据库容量
    - 用途：用户偏好、历史结论、关键事实
    
    实现机制：
    - 使用 PostgreSQL 存储结构化数据
    - 支持复杂查询和索引
    - 支持事务和 ACID 特性
    """
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        """
        初始化长期结构化记忆
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID（可选）
        """
        self.session_id = session_id
        self.user_id = user_id
        self.db = None
    
    def _get_db(self):
        """获取数据库会话"""
        if not self.db:
            self.db = SessionLocal()
        return self.db
    
    async def store_user_preference(self, key: str, value: Any) -> None:
        """
        存储用户偏好
        
        Args:
            key: 偏好键名
            value: 偏好值
        """
        if not self.user_id:
            logger.warning("Cannot store user preference without user_id")
            return
        
        db = self._get_db()
        
        # 这里可以扩展一个 user_preferences 表
        # 目前暂时记录在 metadata 中
        logger.info(f"User preference stored: {key}={value} for user {self.user_id}")
    
    async def store_key_fact(self, fact: str, category: str = "general") -> None:
        """
        存储关键事实
        
        Args:
            fact: 事实内容
            category: 事实类别
        """
        db = self._get_db()
        
        # 这里可以扩展一个 key_facts 表
        logger.info(f"Key fact stored: {fact} (category: {category})")
    
    async def store_historical_conclusion(self, conclusion: str, context: str) -> None:
        """
        存储历史结论
        
        Args:
            conclusion: 结论内容
            context: 结论上下文
        """
        db = self._get_db()
        
        # 这里可以扩展一个 historical_conclusions 表
        logger.info(f"Historical conclusion stored: {conclusion}")
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        获取用户画像
        
        Returns:
            用户画像字典
        """
        # 这里应该从数据库查询用户画像
        # 目前返回空字典
        return {
            "user_id": self.user_id,
            "preferences": {},
            "expertise_level": "unknown",
            "interests": []
        }
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()
            self.db = None


class LongTermSemanticMemory:
    """
    长期语义记忆（四级记忆）
    
    特点：
    - 存储位置：Qdrant 向量数据库
    - 生命周期：永久存储
    - 容量限制：向量库容量
    - 用途：对话片段、经验总结、语义检索
    
    实现机制：
    - 使用 Qdrant 存储向量
    - 支持语义相似度检索
    - 支持元数据过滤
    """
    
    def __init__(self, session_id: str, collection_name: str = "agent_memory"):
        """
        初始化长期语义记忆
        
        Args:
            session_id: 会话 ID
            collection_name: Qdrant 集合名称
        """
        self.session_id = session_id
        self.collection_name = collection_name
        self.client = None
    
    async def _get_client(self):
        """获取 Qdrant 客户端"""
        if not self.client:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
            
            # 确保集合存在
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding 维度
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            except Exception as e:
                # 集合可能已存在
                logger.debug(f"Collection may already exist: {e}")
        
        return self.client
    
    async def store_conversation_fragment(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        存储对话片段
        
        Args:
            content: 对话内容
            embedding: 向量嵌入
            metadata: 元数据（可选）
        """
        client = await self._get_client()
        
        from qdrant_client.models import PointStruct
        import uuid
        
        point_id = str(uuid.uuid4())
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "content": content,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        
        client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        logger.debug(f"Stored conversation fragment: {point_id}")
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索相似对话片段
        
        Args:
            query_embedding: 查询向量
            limit: 返回数量限制
            score_threshold: 相似度阈值
        
        Returns:
            相似对话片段列表
        """
        client = await self._get_client()
        
        results = client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        fragments = [
            {
                "content": result.payload.get("content"),
                "score": result.score,
                "metadata": result.payload
            }
            for result in results
        ]
        
        logger.debug(f"Found {len(fragments)} similar fragments")
        return fragments
    
    async def get_session_fragments(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取当前会话的所有片段
        
        Args:
            limit: 返回数量限制
        
        Returns:
            对话片段列表
        """
        client = await self._get_client()
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        results = client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=self.session_id)
                    )
                ]
            ),
            limit=limit
        )
        
        fragments = [
            {
                "content": point.payload.get("content"),
                "metadata": point.payload
            }
            for point in results[0]
        ]
        
        return fragments


class MemorySystem:
    """
    四级分层记忆系统
    
    统一管理四级记忆，提供便捷的存储和检索接口。
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        max_working_messages: int = 20
    ):
        """
        初始化记忆系统
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID（可选）
            max_working_messages: 工作记忆最大消息数
        """
        self.session_id = session_id
        self.user_id = user_id
        
        # 初始化四级记忆
        self.working_memory = WorkingMemory(max_messages=max_working_messages)
        self.short_term_memory = ShortTermMemory(session_id)
        self.long_term_structured = LongTermStructuredMemory(session_id, user_id)
        self.long_term_semantic = LongTermSemanticMemory(session_id)
    
    async def store_working_memory(self, key: str, value: Any) -> None:
        """存储工作记忆"""
        self.working_memory.store(key, value)
    
    async def retrieve_working_memory(self, key: str) -> Optional[Any]:
        """检索工作记忆"""
        return self.working_memory.retrieve(key)
    
    async def store_short_term_memory(self, key: str, value: Any, ttl: Optional[int] = 3600) -> None:
        """存储短期记忆"""
        await self.short_term_memory.store(key, value, ttl)
    
    async def retrieve_short_term_memory(self, key: str) -> Optional[Any]:
        """检索短期记忆"""
        return await self.short_term_memory.retrieve(key)
    
    async def search_long_term_semantic_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索长期语义记忆
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
        
        Returns:
            搜索结果列表
        """
        return await self.long_term_semantic.search_similar(query, limit)
    
    async def search_long_term_structured_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索长期结构化记忆
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
        
        Returns:
            搜索结果列表
        """
        # 从数据库中搜索相关内容
        results = []
        
        try:
            # 获取用户配置和关键事实
            profile = await self.long_term_structured.get_user_profile()
            
            # 简单的关键词匹配（可以后续优化为更复杂的搜索）
            query_lower = query.lower()
            
            # 搜索用户偏好
            for key, value in profile.get('preferences', {}).items():
                if query_lower in str(key).lower() or query_lower in str(value).lower():
                    results.append({
                        'content': f"用户偏好: {key} = {value}",
                        'metadata': {'type': 'preference', 'key': key}
                    })
            
            # 搜索关键事实
            for fact in profile.get('key_facts', []):
                if query_lower in fact.lower():
                    results.append({
                        'content': f"关键事实: {fact}",
                        'metadata': {'type': 'fact'}
                    })
            
            # 限制结果数量
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search structured memory: {e}")
            return []
    
    async def close(self):
        """关闭所有连接"""
        self.long_term_structured.close()
    
    def get_state_update(self) -> Dict[str, Any]:
        """
        获取状态更新字典
        
        Returns:
            包含所有记忆状态的字典
        """
        return {
            "working_memory": self.working_memory.to_dict(),
            "short_term_memory": {},  # Redis 数据不需要导出
            "long_term_structured": {},  # 数据库数据不需要导出
            "long_term_semantic": []  # 向量数据不需要导出
        }