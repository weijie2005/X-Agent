"""
Agent 服务层

本模块封装 Agent 执行逻辑，提供给路由层调用。
"""
from typing import Dict, Any, Optional, AsyncIterator, List
import logging
from uuid import uuid4

from app.agent.core.agent_executor import AgentExecutor
from app.models.database import SessionLocal
from app.models.tables import Message, MessageRole

logger = logging.getLogger(__name__)


_agent_executor = None


def get_agent_executor() -> AgentExecutor:
    """
    获取 Agent 执行器单例
    
    Returns:
        AgentExecutor 实例
    
    注意：
        如果未初始化，返回未初始化checkpoint的实例
        推荐使用 init_agent_executor() 进行异步初始化
    """
    global _agent_executor
    if _agent_executor is None:
        logger.warning("AgentExecutor not initialized, creating without checkpoint setup")
        _agent_executor = AgentExecutor()
    return _agent_executor


async def init_agent_executor() -> AgentExecutor:
    """
    异步初始化 Agent 执行器
    
    推荐在应用启动时调用，确保 checkpoint 完全初始化。
    
    Returns:
        初始化完成的 AgentExecutor 实例
    
    使用示例：
        executor = await init_agent_executor()
    """
    global _agent_executor
    if _agent_executor is None:
        logger.info("Initializing AgentExecutor with checkpoint setup...")
        _agent_executor = await AgentExecutor.create()
        logger.info("AgentExecutor initialized successfully")
    return _agent_executor


async def close_agent_executor():
    """
    清理 Agent 执行器资源
    
    在应用关闭时调用，关闭连接池等资源
    """
    global _agent_executor
    if _agent_executor and hasattr(_agent_executor, 'close'):
        try:
            await _agent_executor.close()
            logger.info("AgentExecutor resources cleaned up")
        except Exception as e:
            logger.error(f"Failed to clean up AgentExecutor: {e}")
    _agent_executor = None


class AgentService:
    """
    Agent 服务类
    
    封装 Agent 执行逻辑，管理会话和消息。
    """
    
    def __init__(self):
        """初始化 Agent 服务"""
        self.executor = get_agent_executor()
    
    async def chat(
        self,
        session_id: str,
        user_input: str,
        user_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行对话
        
        Args:
            session_id: 会话 ID
            user_input: 用户输入
            user_id: 用户 ID（可选）
            knowledge_base_id: 知识库 ID（可选）
            document_ids: 文档ID列表（可选）
        
        Returns:
            执行结果字典
        """
        logger.info(f"Processing chat for session: {session_id}")
        
        # 保存用户消息到数据库
        db = SessionLocal()
        try:
            user_message = Message(
                session_id=session_id,
                role=MessageRole.USER,
                content=user_input
            )
            db.add(user_message)
            db.commit()
        finally:
            db.close()
        
        # 执行 Agent
        result = await self.executor.run(
            session_id=session_id,
            user_input=user_input,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            document_ids=document_ids,
            metadata={"source": "api"}
        )
        
        # 保存助手消息到数据库
        if result.get("success"):
            db = SessionLocal()
            try:
                assistant_message = Message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=result.get("output", "")
                )
                db.add(assistant_message)
                db.commit()
            finally:
                db.close()
        
        return result
    
    async def stream_chat(
        self,
        session_id: str,
        user_input: str,
        user_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> AsyncIterator[str]:
        """
        流式执行对话
        
        Args:
            session_id: 会话 ID
            user_input: 用户输入
            user_id: 用户 ID（可选）
            knowledge_base_id: 知识库 ID（可选）
            document_ids: 文档ID列表（可选）
        
        Yields:
            SSE 格式的消息
        """
        logger.info(f"Streaming chat for session: {session_id}")
        
        # 确保session存在，如果不存在则创建
        db = SessionLocal()
        try:
            from app.models.tables import Session
            from datetime import datetime
            
            # 检查session是否存在
            existing_session = db.query(Session).filter(Session.id == session_id).first()
            if not existing_session:
                # 创建新session，标题暂时为空，后续根据用户输入生成
                new_session = Session(
                    id=session_id,
                    title=f"新会话",
                    user_id=user_id
                )
                db.add(new_session)
                db.commit()
                logger.info(f"Created new session: {session_id}")
            else:
                # 检查是否需要更新标题（如果标题是默认标题）
                if existing_session.title and existing_session.title.startswith("Chat Session"):
                    # 根据用户输入生成标题（取前20个字符）
                    new_title = user_input[:20] + ("..." if len(user_input) > 20 else "")
                    existing_session.title = new_title
                    db.commit()
                    logger.info(f"Updated session title to: {new_title}")
        finally:
            db.close()
        
        # 检查是否是第一条消息，如果是则生成标题
        db = SessionLocal()
        try:
            from app.models.tables import Session, Message
            
            # 查询该会话的消息数量
            message_count = db.query(Message).filter(Message.session_id == session_id).count()
            
            # 如果是第一条消息，生成标题
            if message_count == 0:
                session = db.query(Session).filter(Session.id == session_id).first()
                if session:
                    # 根据用户输入生成标题（取前20个字符）
                    new_title = user_input[:20] + ("..." if len(user_input) > 20 else "")
                    session.title = new_title
                    db.commit()
                    logger.info(f"Generated session title from first message: {new_title}")
        finally:
            db.close()
        
        # 保存用户消息
        db = SessionLocal()
        try:
            user_message = Message(
                session_id=session_id,
                role=MessageRole.USER,
                content=user_input
            )
            db.add(user_message)
            db.commit()
        finally:
            db.close()
        
        # 流式执行 Agent
        full_output = ""
        reasoning_steps = []
        
        async for event in self.executor.stream(
            session_id=session_id,
            user_input=user_input,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            document_ids=document_ids,
            metadata={"source": "api_stream"}
        ):
            # 格式化为 SSE 消息
            import json
            
            # 处理AIMessage等不可序列化的对象
            def serialize_event(obj):
                """递归处理事件数据，将不可序列化的对象转换为字符串"""
                if isinstance(obj, dict):
                    return {k: serialize_event(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_event(item) for item in obj]
                elif hasattr(obj, 'content'):
                    # 处理AIMessage、HumanMessage等LangChain消息对象
                    return {
                        'type': obj.__class__.__name__,
                        'content': obj.content if hasattr(obj, 'content') else str(obj)
                    }
                elif hasattr(obj, '__dict__'):
                    # 其他对象转换为字典
                    return str(obj)
                else:
                    return obj
            
            serialized_event = serialize_event(event)
            
            # 提取 reasoning_steps
            if event.get("event") == "update":
                data = event.get("data", {})
                if isinstance(data, dict):
                    for node_name, state_update in data.items():
                        if isinstance(state_update, dict):
                            if "reasoning_steps" in state_update:
                                reasoning_steps = state_update["reasoning_steps"]
                                # 添加 reasoning_steps 到响应中
                                serialized_event["data"]["reasoning_steps"] = reasoning_steps
            
            yield f"data: {json.dumps(serialized_event)}\n\n"
            
            # 收集完整输出
            if event.get("event") == "update":
                data = event.get("data", {})
                if isinstance(data, dict):
                    for node_name, state_update in data.items():
                        if isinstance(state_update, dict):
                            if "current_output" in state_update:
                                full_output = state_update["current_output"]
        
        # 保存助手消息
        if full_output:
            db = SessionLocal()
            try:
                assistant_message = Message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=full_output
                )
                db.add(assistant_message)
                db.commit()
            finally:
                db.close()
        
        # 发送完成标记
        yield "data: [DONE]\n\n"