"""
Agent 工具模块

本模块实现了 Agent 的所有工具能力，包括：
1. 计算器工具（安全数学表达式解析）
2. 文档解析工具（PDF、Word、Excel）
3. Tavily 联网搜索工具
4. Python 代码沙箱执行工具（E2B）
5. 记忆搜索工具

设计原则：
- 安全第一：所有工具都经过参数校验和权限检查
- 可审计：所有工具调用都有日志记录
- 可控：工具执行有超时限制和资源限制
- 可扩展：易于添加新工具
"""
from app.agent.tools.base import BaseTool, ToolResult, ToolRegistry
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.document_parser import DocumentParserTool
from app.agent.tools.web_search import WebSearchTool
from app.agent.tools.python_executor import PythonExecutorTool
from app.agent.tools.memory_search import MemorySearchTool

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "CalculatorTool",
    "DocumentParserTool",
    "WebSearchTool",
    "PythonExecutorTool",
    "MemorySearchTool",
]