"""
工具基础类和注册中心

提供工具的基础抽象类和统一注册管理。
"""
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
import logging
import time
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolResult:
    """
    工具执行结果
    
    封装工具执行的返回值和元数据。
    """
    
    def __init__(
        self,
        success: bool,
        output: Any,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        初始化工具结果
        
        Args:
            success: 是否成功
            output: 输出结果
            error: 错误信息（如果失败）
            metadata: 元数据（执行时间、资源使用等）
        """
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.success:
            return f"ToolResult(success=True, output={self.output})"
        else:
            return f"ToolResult(success=False, error={self.error})"


class BaseTool(ABC):
    """
    工具基类
    
    所有工具都必须继承此类并实现 execute 方法。
    """
    
    def __init__(self, name: str, description: str):
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description
        self.enabled = True
        self.timeout = 30  # 默认超时 30 秒
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
        
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    @abstractmethod
    def validate_params(self, **kwargs) -> bool:
        """
        验证参数
        
        Args:
            **kwargs: 工具参数
        
        Returns:
            bool: 参数是否有效
        
        Raises:
            ValueError: 参数无效时抛出
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的 JSON Schema
        
        Returns:
            工具的参数 schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数 schema（子类可覆盖）
        
        Returns:
            参数 schema
        """
        return {
            "type": "object",
            "properties": {}
        }
    
    def log_execution(self, args: Dict[str, Any], result: ToolResult, duration: float):
        """
        记录工具执行日志
        
        Args:
            args: 执行参数
            result: 执行结果
            duration: 执行时长（秒）
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "tool": self.name,
            "args": args,
            "success": result.success,
            "duration": duration
        }
        
        if result.success:
            logger.info(f"Tool executed: {json.dumps(log_data)}")
        else:
            logger.error(f"Tool failed: {json.dumps(log_data)}, error: {result.error}")


class ToolRegistry:
    """
    工具注册中心
    
    统一管理所有工具，提供注册、查询、执行等功能。
    """
    
    def __init__(self):
        """初始化工具注册中心"""
        self._tools: Dict[str, BaseTool] = {}
        self._validators: List[Callable] = []
    
    def register(self, tool: BaseTool):
        """
        注册工具
        
        Args:
            tool: 工具实例
        
        Raises:
            ValueError: 工具已存在
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        
        self._tools[tool.name] = tool
        logger.info(f"Tool registered: {tool.name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            name: 工具名称
        
        Returns:
            工具实例，如果不存在返回 None
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """
        列出所有工具名称
        
        Returns:
            工具名称列表
        """
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的 schema
        
        Returns:
            工具 schema 列表
        """
        return [tool.get_schema() for tool in self._tools.values()]
    
    def add_validator(self, validator: Callable):
        """
        添加全局验证器
        
        Args:
            validator: 验证函数，接收 (tool_name, args) 参数，返回 bool
        """
        self._validators.append(validator)
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            name: 工具名称
            **kwargs: 工具参数
        
        Returns:
            ToolResult: 执行结果
        """
        # 检查工具是否存在
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' not found"
            )
        
        # 检查工具是否启用
        if not tool.enabled:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' is disabled"
            )
        
        # 执行全局验证器
        for validator in self._validators:
            if not validator(name, kwargs):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Tool '{name}' validation failed"
                )
        
        # 验证参数
        try:
            tool.validate_params(**kwargs)
        except ValueError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Parameter validation failed: {str(e)}"
            )
        
        # 执行工具
        start_time = time.time()
        try:
            result = await tool.execute(**kwargs)
            duration = time.time() - start_time
            
            # 记录日志
            tool.log_execution(kwargs, result, duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_result = ToolResult(
                success=False,
                output=None,
                error=f"Tool execution error: {str(e)}"
            )
            
            # 记录错误日志
            tool.log_execution(kwargs, error_result, duration)
            
            return error_result


# 全局工具注册中心实例
_global_registry = None


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册中心
    
    Returns:
        ToolRegistry 实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry