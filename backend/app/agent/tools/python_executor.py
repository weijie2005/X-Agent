"""
Python 代码沙箱执行工具

使用 E2B 沙箱执行 Python 代码，禁止本地宿主机执行。
"""
import os
import logging
from typing import Dict, Any, Optional
import json
import traceback

from app.agent.tools.base import BaseTool, ToolResult
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PythonExecutorTool(BaseTool):
    """
    Python 代码执行工具
    
    功能：
    - 执行 Python 代码
    - 支持数据分析、统计计算、数据处理
    - 支持常用库：numpy、pandas、matplotlib
    
    安全机制：
    - 使用 E2B 沙箱，禁止本地执行
    - 执行时间限制
    - 内存限制
    - 网络隔离
    """
    
    # 最大代码长度
    MAX_CODE_LENGTH = 10000
    
    # 执行超时（秒）
    EXECUTION_TIMEOUT = 30
    
    # 允许的库（白名单）
    ALLOWED_LIBRARIES = [
        'numpy', 'pandas', 'matplotlib', 'scipy',
        'sklearn', 'statsmodels', 'seaborn',
        'json', 'math', 'random', 'datetime',
        'collections', 'itertools', 'functools',
        're', 'string', 'textwrap',
    ]
    
    # 禁止的模块（黑名单）
    FORBIDDEN_MODULES = [
        'os', 'sys', 'subprocess', 'commands',
        'socket', 'requests', 'urllib',
        'pickle', 'marshal', 'shelve',
        '__builtin__', 'builtins',
        'importlib', 'imp',
    ]
    
    def __init__(self):
        """初始化 Python 执行工具"""
        super().__init__(
            name="python_executor",
            description="执行 Python 代码，用于数据分析、统计计算和数据处理"
        )
        self.timeout = self.EXECUTION_TIMEOUT
        
        # 获取 E2B API Key
        self.api_key = os.getenv('E2B_API_KEY', '')
        
        if not self.api_key:
            logger.warning("E2B_API_KEY not configured, code execution will be limited")
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证参数
        
        Args:
            code: Python 代码
            timeout: 执行超时（可选）
        
        Returns:
            bool: 参数是否有效
        
        Raises:
            ValueError: 参数无效
        """
        code = kwargs.get('code')
        
        if not code:
            raise ValueError("Parameter 'code' is required")
        
        if not isinstance(code, str):
            raise ValueError("Parameter 'code' must be a string")
        
        if len(code) > self.MAX_CODE_LENGTH:
            raise ValueError(f"Code too long (max {self.MAX_CODE_LENGTH} characters)")
        
        # 检查禁止的模块
        code_lower = code.lower()
        for module in self.FORBIDDEN_MODULES:
            if f'import {module}' in code_lower or f'from {module}' in code_lower:
                raise ValueError(f"Forbidden module detected: {module}")
        
        return True
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行 Python 代码
        
        Args:
            code: Python 代码
            timeout: 执行超时（可选）
        
        Returns:
            ToolResult: 执行结果
        """
        code = kwargs.get('code')
        timeout = kwargs.get('timeout', self.EXECUTION_TIMEOUT)
        
        # 检查 API Key
        if not self.api_key:
            return ToolResult(
                success=False,
                output=None,
                error="E2B_API_KEY not configured. Please set E2B_API_KEY in .env file."
            )
        
        try:
            # 尝试使用 E2B SDK
            try:
                from e2b import Sandbox
                
                # 创建沙箱
                sandbox = Sandbox(api_key=self.api_key, timeout=timeout)
                
                # 执行代码
                execution = sandbox.run_code(code)
                
                # 获取结果
                stdout = execution.stdout
                stderr = execution.stderr
                exit_code = execution.exit_code
                
                # 关闭沙箱
                sandbox.close()
                
                if exit_code == 0:
                    return ToolResult(
                        success=True,
                        output={
                            "stdout": stdout,
                            "stderr": stderr,
                            "exit_code": exit_code
                        },
                        metadata={
                            "timeout": timeout,
                            "code_length": len(code)
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        output={
                            "stdout": stdout,
                            "stderr": stderr,
                            "exit_code": exit_code
                        },
                        error=f"Code execution failed with exit code {exit_code}"
                    )
                
            except ImportError:
                logger.warning("e2b-sdk not installed, using fallback method")
                
                # 回退方案：使用受限的本地执行（仅用于开发测试）
                # 生产环境必须使用 E2B
                if os.getenv('ALLOW_LOCAL_EXECUTION', 'false').lower() == 'true':
                    logger.warning("Using local execution (DEVELOPMENT ONLY)")
                    return await self._execute_locally(code, timeout)
                else:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="e2b-sdk not installed. Please install it: pip install e2b"
                    )
            
        except Exception as e:
            logger.error(f"Python executor tool error: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Code execution failed: {str(e)}"
            )
    
    async def _execute_locally(self, code: str, timeout: int) -> ToolResult:
        """
        本地执行代码（仅用于开发测试，生产环境禁用）
        
        Args:
            code: Python 代码
            timeout: 执行超时
        
        Returns:
            ToolResult: 执行结果
        """
        import sys
        from io import StringIO
        import signal
        
        # 创建受限的执行环境
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'reversed': reversed,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'bool': bool,
                'json': json,
            }
        }
        
        # 添加允许的库
        try:
            import numpy as np
            safe_globals['np'] = np
            safe_globals['numpy'] = np
        except ImportError:
            pass
        
        try:
            import pandas as pd
            safe_globals['pd'] = pd
            safe_globals['pandas'] = pd
        except ImportError:
            pass
        
        # 捕获标准输出
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # 执行代码
            exec(code, safe_globals)
            
            # 获取输出
            output = captured_output.getvalue()
            
            return ToolResult(
                success=True,
                output={
                    "stdout": output,
                    "stderr": "",
                    "exit_code": 0
                },
                metadata={
                    "timeout": timeout,
                    "code_length": len(code),
                    "execution_mode": "local"
                }
            )
            
        except Exception as e:
            # 获取错误信息
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            
            return ToolResult(
                success=False,
                output={
                    "stdout": captured_output.getvalue(),
                    "stderr": error_msg,
                    "exit_code": 1
                },
                error=error_msg
            )
        finally:
            # 恢复标准输出
            sys.stdout = old_stdout
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 schema"""
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码"
                },
                "timeout": {
                    "type": "integer",
                    "description": "执行超时（秒）",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 60
                }
            },
            "required": ["code"]
        }