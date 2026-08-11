"""
Harness 工程生产级管控系统

实现企业级生产能力：安全、可控、可审计、可自愈。

核心组件：
1. SecurityInterceptor: 安全拦截层（Prompt注入防护、参数清洗、脱敏）
2. AuditSystem: 全链路审计系统（对话、工具调用、LLM请求日志）
3. FaultToleranceSystem: 容错自愈系统（超时重试、异常降级、任务恢复）
4. ContextManager: 上下文工程管控（token裁剪、摘要压缩、记忆清理）
5. ComplianceValidator: 输出合规校验（敏感内容检测、事实一致性）
6. RateLimiter: 限流熔断降级（防止大并发打垮服务）
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(Enum):
    """审计事件类型"""
    AGENT_REQUEST = "agent_request"
    TOOL_CALL = "tool_call"
    LLM_REQUEST = "llm_request"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ERROR = "system_error"


class HarnessConfig:
    """
    Harness 配置
    
    集中管理所有 Harness 组件的配置。
    """
    
    def __init__(self):
        """初始化配置"""
        # 安全配置
        self.enable_security_interceptor = True
        self.enable_prompt_injection_protection = True
        self.enable_parameter_sanitization = True
        self.enable_data_masking = True
        self.enable_tool_whitelist = True
        self.enable_path_validation = True
        
        # 审计配置
        self.enable_audit_system = True
        self.audit_log_level = "INFO"
        self.audit_retention_days = 90
        
        # 容错配置
        self.enable_fault_tolerance = True
        self.max_retry_attempts = 3
        self.retry_delay_seconds = 1
        self.enable_circuit_breaker = True
        self.circuit_breaker_threshold = 5
        
        # 上下文管理配置
        self.enable_context_management = True
        self.max_context_tokens = 4000
        self.enable_auto_summary = True
        self.memory_expiry_days = 30
        
        # 合规配置
        self.enable_compliance_validation = True
        self.sensitive_keywords = []
        self.enable_fact_checking = False
        
        # 限流配置
        self.enable_rate_limiter = True
        self.max_requests_per_minute = 60
        self.max_requests_per_hour = 1000
        
        logger.info("Initialized HarnessConfig")


# 全局配置实例
harness_config = HarnessConfig()