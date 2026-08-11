"""
工具注册中心

统一注册和管理所有工具。
"""
import logging
from typing import List, Dict, Any

from app.agent.tools.base import BaseTool, ToolRegistry, get_tool_registry
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.document_parser import DocumentParserTool
from app.agent.tools.web_search import WebSearchTool
from app.agent.tools.python_executor import PythonExecutorTool
from app.agent.tools.memory_search import MemorySearchTool

logger = logging.getLogger(__name__)


def register_all_tools() -> ToolRegistry:
    """
    注册所有工具
    
    Returns:
        ToolRegistry: 工具注册中心
    """
    registry = get_tool_registry()
    
    # 检查是否已经注册
    if registry.list_tools():
        logger.info("Tools already registered")
        return registry
    
    # 注册计算器工具
    calculator = CalculatorTool()
    registry.register(calculator)
    
    # 注册文档解析工具
    document_parser = DocumentParserTool()
    registry.register(document_parser)
    
    # 注册联网搜索工具
    web_search = WebSearchTool()
    registry.register(web_search)
    
    # 注册 Python 执行工具
    python_executor = PythonExecutorTool()
    registry.register(python_executor)
    
    # 注册记忆搜索工具
    memory_search = MemorySearchTool()
    registry.register(memory_search)
    
    logger.info(f"Registered {len(registry.list_tools())} tools")
    
    return registry


def get_enabled_tools() -> List[str]:
    """
    获取已启用的工具列表
    
    Returns:
        工具名称列表
    """
    registry = get_tool_registry()
    return [
        name for name in registry.list_tools()
        if registry.get(name).enabled
    ]


def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    获取所有工具的 schema
    
    Returns:
        工具 schema 列表
    """
    registry = get_tool_registry()
    return registry.get_all_schemas()


# 自动注册所有工具（在导入时执行）
register_all_tools()