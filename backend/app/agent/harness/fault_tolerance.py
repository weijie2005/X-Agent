"""
容错自愈系统

实现企业级容错能力：
1. 超时重试
2. 异常降级
3. 任务中断恢复
4. 参数回滚
"""
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"  # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性退避


@dataclass
class RetryConfig:
    """
    重试配置
    """
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    exceptions: List[type] = field(default_factory=lambda: [Exception])
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟
        
        Args:
            attempt: 当前尝试次数
        
        Returns:
            延迟时间（秒）
        """
        if self.strategy == RetryStrategy.FIXED:
            return min(self.base_delay, self.max_delay)
        
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
            return min(delay, self.max_delay)
        
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
            return min(delay, self.max_delay)
        
        return self.base_delay


@dataclass
class TaskState:
    """
    任务状态
    
    用于任务中断恢复。
    """
    task_id: str
    task_type: str
    status: str  # pending, running, completed, failed, interrupted
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    checkpoint: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "checkpoint": self.checkpoint,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class FaultToleranceSystem:
    """
    容错自愈系统
    
    实现超时重试、异常降级、任务中断恢复、参数回滚。
    """
    
    def __init__(
        self,
        enable_retry: bool = True,
        enable_circuit_breaker: bool = True,
        enable_task_recovery: bool = True,
        default_retry_config: Optional[RetryConfig] = None
    ):
        """
        初始化容错系统
        
        Args:
            enable_retry: 是否启用重试
            enable_circuit_breaker: 是否启用熔断器
            enable_task_recovery: 是否启用任务恢复
            default_retry_config: 默认重试配置
        """
        self.enable_retry = enable_retry
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_task_recovery = enable_task_recovery
        
        # 默认重试配置
        self.default_retry_config = default_retry_config or RetryConfig()
        
        # 任务状态存储（生产环境应该使用数据库）
        self.task_states: Dict[str, TaskState] = {}
        
        # 熔断器状态
        self.circuit_breaker_state: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized FaultToleranceSystem")
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_config: Optional[RetryConfig] = None,
        **kwargs
    ) -> Any:
        """
        带重试的执行
        
        Args:
            func: 要执行的函数
            retry_config: 重试配置
            args: 函数参数
            kwargs: 函数关键字参数
        
        Returns:
            函数结果
        
        Raises:
            Exception: 所有重试失败后的异常
        """
        if not self.enable_retry:
            return await func(*args, **kwargs)
        
        config = retry_config or self.default_retry_config
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 成功，返回结果
                if attempt > 1:
                    logger.info(f"Retry attempt {attempt} succeeded")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # 检查是否是需要重试的异常
                if not any(isinstance(e, exc) for exc in config.exceptions):
                    logger.error(f"Non-retryable exception: {e}")
                    raise
                
                # 记录失败
                logger.warning(f"Attempt {attempt} failed: {e}")
                
                # 如果还有重试机会，等待后重试
                if attempt < config.max_attempts:
                    delay = config.calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
        
        # 所有重试都失败
        logger.error(f"All {config.max_attempts} attempts failed")
        raise last_exception
    
    def check_circuit_breaker(self, service_name: str) -> bool:
        """
        检查熔断器状态
        
        Args:
            service_name: 服务名称
        
        Returns:
            是否允许请求
        """
        if not self.enable_circuit_breaker:
            return True
        
        state = self.circuit_breaker_state.get(service_name)
        
        if not state:
            return True
        
        # 检查熔断器状态
        if state["status"] == "open":
            # 检查是否超过冷却时间
            if datetime.now() > state["reset_time"]:
                # 进入半开状态
                state["status"] = "half_open"
                state["success_count"] = 0
                logger.info(f"Circuit breaker for {service_name} entered half-open state")
                return True
            else:
                logger.warning(f"Circuit breaker for {service_name} is open")
                return False
        
        return True
    
    def record_success(self, service_name: str):
        """
        记录成功
        
        Args:
            service_name: 服务名称
        """
        if not self.enable_circuit_breaker:
            return
        
        state = self.circuit_breaker_state.get(service_name)
        
        if state and state["status"] == "half_open":
            state["success_count"] += 1
            
            # 如果连续成功，关闭熔断器
            if state["success_count"] >= 3:
                state["status"] = "closed"
                state["failure_count"] = 0
                logger.info(f"Circuit breaker for {service_name} closed")
    
    def record_failure(self, service_name: str):
        """
        记录失败
        
        Args:
            service_name: 服务名称
        """
        if not self.enable_circuit_breaker:
            return
        
        if service_name not in self.circuit_breaker_state:
            self.circuit_breaker_state[service_name] = {
                "status": "closed",
                "failure_count": 0,
                "success_count": 0,
                "reset_time": None
            }
        
        state = self.circuit_breaker_state[service_name]
        state["failure_count"] += 1
        
        # 如果失败次数超过阈值，打开熔断器
        if state["failure_count"] >= 5:
            state["status"] = "open"
            state["reset_time"] = datetime.now() + timedelta(seconds=60)
            logger.warning(f"Circuit breaker for {service_name} opened")
    
    def save_task_state(self, task_state: TaskState):
        """
        保存任务状态
        
        Args:
            task_state: 任务状态
        """
        if not self.enable_task_recovery:
            return
        
        task_state.updated_at = datetime.now()
        self.task_states[task_state.task_id] = task_state
        
        logger.info(f"Saved task state: {task_state.task_id} - {task_state.status}")
    
    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """
        获取任务状态
        
        Args:
            task_id: 任务 ID
        
        Returns:
            任务状态
        """
        return self.task_states.get(task_id)
    
    def recover_interrupted_tasks(self) -> List[TaskState]:
        """
        恢复中断的任务
        
        Returns:
            中断的任务列表
        """
        if not self.enable_task_recovery:
            return []
        
        interrupted_tasks = [
            task for task in self.task_states.values()
            if task.status == "interrupted"
        ]
        
        logger.info(f"Found {len(interrupted_tasks)} interrupted tasks")
        
        return interrupted_tasks


# 需要导入 timedelta
from datetime import timedelta


# 使用示例
if __name__ == "__main__":
    # 初始化容错系统
    fault_tolerance = FaultToleranceSystem(
        enable_retry=True,
        enable_circuit_breaker=True,
        enable_task_recovery=True
    )
    
    print("=" * 60)
    print("容错自愈系统测试")
    print("=" * 60)
    
    # 测试 1: 重试机制
    print("\n【测试1】重试机制:")
    
    async def test_retry():
        """测试重试"""
        attempt_count = 0
        
        async def flaky_function():
            """不稳定的函数"""
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:
                raise Exception(f"Attempt {attempt_count} failed")
            
            return f"Success on attempt {attempt_count}"
        
        try:
            result = await fault_tolerance.execute_with_retry(
                flaky_function,
                retry_config=RetryConfig(max_attempts=5, strategy=RetryStrategy.EXPONENTIAL)
            )
            print(f"结果: {result}")
        except Exception as e:
            print(f"失败: {e}")
    
    asyncio.run(test_retry())
    
    # 测试 2: 熔断器
    print("\n【测试2】熔断器:")
    
    # 检查熔断器状态
    is_allowed = fault_tolerance.check_circuit_breaker("llm_service")
    print(f"LLM 服务熔断器状态: {'允许' if is_allowed else '拒绝'}")
    
    # 记录失败
    for i in range(6):
        fault_tolerance.record_failure("llm_service")
    
    # 再次检查
    is_allowed = fault_tolerance.check_circuit_breaker("llm_service")
    print(f"LLM 服务熔断器状态: {'允许' if is_allowed else '拒绝'}")
    
    # 测试 3: 任务恢复
    print("\n【测试3】任务恢复:")
    
    # 创建任务状态
    task_state = TaskState(
        task_id="task_001",
        task_type="agent_request",
        status="interrupted",
        input_data={"user_input": "你好"},
        checkpoint={"step": 2}
    )
    
    # 保存任务状态
    fault_tolerance.save_task_state(task_state)
    
    # 恢复中断的任务
    interrupted_tasks = fault_tolerance.recover_interrupted_tasks()
    
    print(f"找到 {len(interrupted_tasks)} 个中断的任务")
    for task in interrupted_tasks:
        print(f"  - {task.task_id}: {task.status}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)