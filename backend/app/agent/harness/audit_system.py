"""
全链路审计系统

实现企业级审计能力：
1. 每轮对话日志落库
2. 每次工具调用日志落库
3. 每次 LLM 请求日志落库
4. 安全违规日志落库
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """审计事件类型"""
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ERROR = "system_error"
    RATE_LIMIT_HIT = "rate_limit_hit"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"


@dataclass
class AuditEvent:
    """
    审计事件
    
    记录所有系统操作的详细信息。
    """
    event_id: str
    event_type: str
    timestamp: str
    session_id: str
    user_id: str
    
    # 事件详情
    action: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    
    # 性能指标
    duration_ms: Optional[float] = None
    token_count: Optional[int] = None
    
    # 安全信息
    security_violations: Optional[List[Dict[str, Any]]] = None
    
    # 错误信息
    error: Optional[str] = None
    error_stack: Optional[str] = None
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditSystem:
    """
    审计系统
    
    全链路审计，所有操作日志落库。
    """
    
    def __init__(
        self,
        enable_database_logging: bool = True,
        enable_file_logging: bool = True,
        log_level: str = "INFO",
        retention_days: int = 90
    ):
        """
        初始化审计系统
        
        Args:
            enable_database_logging: 是否启用数据库日志
            enable_file_logging: 是否启用文件日志
            log_level: 日志级别
            retention_days: 日志保留天数
        """
        self.enable_database_logging = enable_database_logging
        self.enable_file_logging = enable_file_logging
        self.log_level = log_level
        self.retention_days = retention_days
        
        # 日志存储（生产环境应该使用数据库）
        self.event_log: List[AuditEvent] = []
        
        logger.info("Initialized AuditSystem")
    
    def log_event(
        self,
        event_type: AuditEventType,
        session_id: str,
        user_id: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        token_count: Optional[int] = None,
        security_violations: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
        error_stack: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        记录审计事件
        
        Args:
            event_type: 事件类型
            session_id: 会话 ID
            user_id: 用户 ID
            action: 操作
            input_data: 输入数据
            output_data: 输出数据
            duration_ms: 耗时（毫秒）
            token_count: Token 数量
            security_violations: 安全违规列表
            error: 错误信息
            error_stack: 错误堆栈
            metadata: 元数据
        
        Returns:
            审计事件
        """
        # 创建事件
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type.value,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_id=user_id,
            action=action,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            token_count=token_count,
            security_violations=security_violations,
            error=error,
            error_stack=error_stack,
            metadata=metadata
        )
        
        # 存储事件
        self.event_log.append(event)
        
        # 记录日志
        if self.enable_file_logging:
            self._log_to_file(event)
        
        # 记录到数据库（生产环境）
        if self.enable_database_logging:
            self._log_to_database(event)
        
        return event
    
    def log_agent_request(
        self,
        session_id: str,
        user_id: str,
        user_input: str,
        duration_ms: Optional[float] = None,
        token_count: Optional[int] = None,
        security_violations: Optional[List[Dict[str, Any]]] = None
    ) -> AuditEvent:
        """
        记录 Agent 请求
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            user_input: 用户输入
            duration_ms: 耗时
            token_count: Token 数量
            security_violations: 安全违规列表
        
        Returns:
            审计事件
        """
        return self.log_event(
            event_type=AuditEventType.AGENT_REQUEST,
            session_id=session_id,
            user_id=user_id,
            action="agent_request",
            input_data={"user_input": user_input},
            duration_ms=duration_ms,
            token_count=token_count,
            security_violations=security_violations
        )
    
    def log_tool_call(
        self,
        session_id: str,
        user_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> AuditEvent:
        """
        记录工具调用
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            tool_name: 工具名称
            tool_args: 工具参数
            tool_result: 工具结果
            duration_ms: 耗时
            error: 错误信息
        
        Returns:
            审计事件
        """
        return self.log_event(
            event_type=AuditEventType.TOOL_CALL,
            session_id=session_id,
            user_id=user_id,
            action=f"tool_call:{tool_name}",
            input_data={"tool_name": tool_name, "tool_args": tool_args},
            output_data=tool_result,
            duration_ms=duration_ms,
            error=error
        )
    
    def log_llm_request(
        self,
        session_id: str,
        user_id: str,
        prompt: str,
        response: Optional[str] = None,
        duration_ms: Optional[float] = None,
        token_count: Optional[int] = None,
        error: Optional[str] = None
    ) -> AuditEvent:
        """
        记录 LLM 请求
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            prompt: Prompt
            response: 响应
            duration_ms: 耗时
            token_count: Token 数量
            error: 错误信息
        
        Returns:
            审计事件
        """
        return self.log_event(
            event_type=AuditEventType.LLM_REQUEST,
            session_id=session_id,
            user_id=user_id,
            action="llm_request",
            input_data={"prompt": prompt},
            output_data={"response": response} if response else None,
            duration_ms=duration_ms,
            token_count=token_count,
            error=error
        )
    
    def log_security_violation(
        self,
        session_id: str,
        user_id: str,
        violation_type: str,
        severity: str,
        message: str,
        details: Dict[str, Any]
    ) -> AuditEvent:
        """
        记录安全违规
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            violation_type: 违规类型
            severity: 严重程度
            message: 消息
            details: 详情
        
        Returns:
            审计事件
        """
        return self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            session_id=session_id,
            user_id=user_id,
            action=f"security_violation:{violation_type}",
            input_data={},
            security_violations=[{
                "type": violation_type,
                "severity": severity,
                "message": message,
                "details": details
            }]
        )
    
    def _log_to_file(self, event: AuditEvent):
        """
        记录到文件
        
        Args:
            event: 审计事件
        """
        log_message = f"[{event.timestamp}] {event.event_type} - {event.action}"
        
        if event.error:
            logger.error(f"{log_message} - Error: {event.error}")
        else:
            logger.info(log_message)
    
    def _log_to_database(self, event: AuditEvent):
        """
        记录到数据库
        
        Args:
            event: 审计事件
        """
        # 生产环境应该实现数据库存储
        # 这里只是示例
        pass
    
    def get_events(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        查询审计事件
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            event_type: 事件类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
        
        Returns:
            审计事件列表
        """
        filtered_events = []
        
        for event in self.event_log:
            # 过滤条件
            if session_id and event.session_id != session_id:
                continue
            
            if user_id and event.user_id != user_id:
                continue
            
            if event_type and event.event_type != event_type.value:
                continue
            
            if start_time:
                event_time = datetime.fromisoformat(event.timestamp)
                if event_time < start_time:
                    continue
            
            if end_time:
                event_time = datetime.fromisoformat(event.timestamp)
                if event_time > end_time:
                    continue
            
            filtered_events.append(event)
            
            if len(filtered_events) >= limit:
                break
        
        return filtered_events
    
    def get_statistics(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            session_id: 会话 ID
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            统计信息
        """
        events = self.get_events(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # 统计各类型事件数量
        event_counts = {}
        for event in events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # 统计平均耗时
        durations = [e.duration_ms for e in events if e.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 统计 Token 数量
        token_counts = [e.token_count for e in events if e.token_count]
        total_tokens = sum(token_counts)
        
        # 统计错误数量
        error_count = sum(1 for e in events if e.error)
        
        # 统计安全违规数量
        security_violation_count = sum(
            len(e.security_violations) 
            for e in events 
            if e.security_violations
        )
        
        return {
            "total_events": len(events),
            "event_counts": event_counts,
            "avg_duration_ms": avg_duration,
            "total_tokens": total_tokens,
            "error_count": error_count,
            "security_violation_count": security_violation_count
        }


# 使用示例
if __name__ == "__main__":
    # 初始化审计系统
    audit_system = AuditSystem(
        enable_database_logging=False,
        enable_file_logging=True
    )
    
    print("=" * 60)
    print("审计系统测试")
    print("=" * 60)
    
    # 测试 1: 记录 Agent 请求
    print("\n【测试1】记录 Agent 请求:")
    event1 = audit_system.log_agent_request(
        session_id="session_001",
        user_id="user_001",
        user_input="你好，请介绍一下 Python",
        duration_ms=123.45,
        token_count=50
    )
    
    print(f"事件 ID: {event1.event_id}")
    print(f"事件类型: {event1.event_type}")
    print(f"时间戳: {event1.timestamp}")
    
    # 测试 2: 记录工具调用
    print("\n【测试2】记录工具调用:")
    event2 = audit_system.log_tool_call(
        session_id="session_001",
        user_id="user_001",
        tool_name="calculator",
        tool_args={"expression": "2 + 2"},
        tool_result={"result": 4},
        duration_ms=10.5
    )
    
    print(f"事件 ID: {event2.event_id}")
    print(f"操作: {event2.action}")
    
    # 测试 3: 记录 LLM 请求
    print("\n【测试3】记录 LLM 请求:")
    event3 = audit_system.log_llm_request(
        session_id="session_001",
        user_id="user_001",
        prompt="请介绍一下 Python",
        response="Python 是一种高级编程语言...",
        duration_ms=500.0,
        token_count=100
    )
    
    print(f"事件 ID: {event3.event_id}")
    print(f"Token 数量: {event3.token_count}")
    
    # 测试 4: 记录安全违规
    print("\n【测试4】记录安全违规:")
    event4 = audit_system.log_security_violation(
        session_id="session_001",
        user_id="user_001",
        violation_type="prompt_injection",
        severity="high",
        message="检测到 Prompt 注入尝试",
        details={"pattern": "ignore previous instructions"}
    )
    
    print(f"事件 ID: {event4.event_id}")
    print(f"违规类型: {event4.action}")
    
    # 测试 5: 查询事件
    print("\n【测试5】查询事件:")
    events = audit_system.get_events(session_id="session_001")
    
    print(f"查询到 {len(events)} 个事件")
    for event in events:
        print(f"  - {event.event_type}: {event.action}")
    
    # 测试 6: 统计信息
    print("\n【测试6】统计信息:")
    stats = audit_system.get_statistics(session_id="session_001")
    
    print(f"总事件数: {stats['total_events']}")
    print(f"平均耗时: {stats['avg_duration_ms']:.2f}ms")
    print(f"总 Token 数: {stats['total_tokens']}")
    print(f"错误数: {stats['error_count']}")
    print(f"安全违规数: {stats['security_violation_count']}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)