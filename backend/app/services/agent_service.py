"""
Agent 服务层

本模块封装 Agent 执行逻辑，提供给路由层调用。
集成 Harness 工程管控，提供安全、可控、可审计的 Agent 执行能力。
"""
from typing import Dict, Any, Optional, AsyncIterator, List
import logging
from uuid import uuid4

from app.agent.core.agent_executor import AgentExecutor
from app.agent.harness.harness import Harness, HarnessResult
from app.models.database import SessionLocal
from app.models.tables import Message, MessageRole
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


_agent_executor = None
_harness_instance = None


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


def get_harness_instance() -> Harness:
    """
    获取 Harness 实例单例
    
    Returns:
        Harness 实例
    
    注意：
        如果未初始化，返回默认配置的 Harness 实例
    """
    global _harness_instance
    if _harness_instance is None:
        logger.info("Initializing Harness with settings...")
        _harness_instance = Harness(
            enable_security_interceptor=settings.HARNESS_ENABLE_SECURITY_INTERCEPTOR,
            enable_prompt_injection_protection=settings.HARNESS_ENABLE_PROMPT_INJECTION_PROTECTION,
            enable_data_masking=settings.HARNESS_ENABLE_DATA_MASKING,
            enable_tool_whitelist=settings.HARNESS_ENABLE_TOOL_WHITELIST,
            enable_path_validation=settings.HARNESS_ENABLE_PATH_VALIDATION,
            allowed_tools=settings.HARNESS_ALLOWED_TOOLS,
            allowed_directories=settings.HARNESS_ALLOWED_DIRECTORIES,
            enable_audit_system=settings.HARNESS_ENABLE_AUDIT_SYSTEM,
            audit_log_level=settings.HARNESS_AUDIT_LOG_LEVEL,
            audit_retention_days=settings.HARNESS_AUDIT_RETENTION_DAYS,
            enable_fault_tolerance=settings.HARNESS_ENABLE_FAULT_TOLERANCE,
            max_retry_attempts=settings.HARNESS_MAX_RETRY_ATTEMPTS,
            enable_circuit_breaker=settings.HARNESS_ENABLE_CIRCUIT_BREAKER,
            enable_rate_limiter=settings.HARNESS_ENABLE_RATE_LIMITER,
            max_requests_per_minute=settings.HARNESS_MAX_REQUESTS_PER_MINUTE
        )
        logger.info("Harness initialized successfully")
    return _harness_instance


class AgentService:
    """
    Agent 服务类
    
    封装 Agent 执行逻辑，管理会话和消息。
    集成 Harness 工程管控，提供安全、可控、可审计的 Agent 执行能力。
    """
    
    def __init__(self):
        """初始化 Agent 服务"""
        self.executor = get_agent_executor()
        self.harness = get_harness_instance() if settings.ENABLE_HARNESS else None
    
    async def chat(
        self,
        session_id: str,
        user_input: str,
        user_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行对话（集成 Harness 管控）
        
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
        
        # 执行 Agent（通过 Harness 管控）
        if self.harness:
            # 使用 Harness 管控执行
            harness_result: HarnessResult = await self.harness.process_agent_request(
                user_input=user_input,
                session_id=session_id,
                user_id=user_id or "anonymous",
                agent_func=self.executor.run,
                knowledge_base_id=knowledge_base_id,
                document_ids=document_ids,
                metadata={"source": "api"}
            )
            
            # 转换 Harness 结果为标准格式
            result = {
                "success": harness_result.success,
                "output": harness_result.data if harness_result.success else "",
                "error": harness_result.error,
                "metadata": {
                    "audit_event_id": harness_result.audit_event_id,
                    "violations_count": len(harness_result.violations),
                    **(harness_result.metadata or {})
                }
            }
            
            # 如果有安全违规，记录详细信息
            if harness_result.violations:
                logger.warning(
                    f"Security violations detected: {len(harness_result.violations)} violations"
                )
                result["violations"] = [
                    {
                        "type": v.violation_type,
                        "severity": v.severity,
                        "message": v.message
                    }
                    for v in harness_result.violations
                ]
        else:
            # 未启用 Harness，直接执行
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
        流式执行对话（集成 Harness 管控）
        
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
        
        # Harness 安全检查（流式场景）
        if self.harness:
            # 执行安全拦截检查
            if self.harness.security_interceptor:
                is_safe, processed_input, violations = self.harness.security_interceptor.intercept_agent_request(
                    user_input, session_id, user_id or "anonymous"
                )
                
                if not is_safe:
                    # 返回安全违规错误
                    import json
                    error_event = {
                        "event": "error",
                        "data": {
                            "error": "Security violation detected",
                            "violations": [
                                {
                                    "type": v.violation_type,
                                    "severity": v.severity,
                                    "message": v.message
                                }
                                for v in violations
                            ]
                        }
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"
                    logger.warning(f"Stream chat blocked due to security violations: {len(violations)}")
                    return
                
                # 使用处理后的输入
                user_input = processed_input
        
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