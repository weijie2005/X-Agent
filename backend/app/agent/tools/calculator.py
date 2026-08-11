"""
计算器工具

使用安全的数学表达式解析，禁止代码注入。
"""
import re
import math
import operator
from typing import Dict, Any, Optional
import logging

from app.agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class SafeExpressionEvaluator:
    """
    安全的数学表达式求值器
    
    使用白名单机制，只允许安全的数学运算。
    禁止：
    - 代码注入（eval、exec、import 等）
    - 危险函数（open、file、__import__ 等）
    - 系统调用（os、sys、subprocess 等）
    """
    
    # 允许的运算符
    OPERATORS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '//': operator.floordiv,
        '%': operator.mod,
        '**': operator.pow,
        '^': operator.xor,  # 注意：Python 中 ^ 是按位异或，不是幂运算
    }
    
    # 允许的数学函数
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        # 数学函数
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'exp': math.exp,
        'ceil': math.ceil,
        'floor': math.floor,
        'pi': math.pi,
        'e': math.e,
    }
    
    # 禁止的关键字（黑名单）
    FORBIDDEN_KEYWORDS = [
        'import', 'exec', 'eval', 'compile', 'open', 'file',
        '__import__', '__builtins__', '__class__', '__bases__',
        '__subclasses__', '__mro__', '__globals__', '__code__',
        'os', 'sys', 'subprocess', 'commands', 'pty', 'spawn',
        'pickle', 'marshal', 'shelve', 'socket', 'requests',
    ]
    
    @classmethod
    def evaluate(cls, expression: str) -> float:
        """
        安全地求值数学表达式
        
        Args:
            expression: 数学表达式字符串
        
        Returns:
            计算结果
        
        Raises:
            ValueError: 表达式包含危险内容或语法错误
        """
        # 1. 预处理：移除空格
        expr = expression.strip()
        
        # 2. 检查黑名单
        expr_lower = expr.lower()
        for keyword in cls.FORBIDDEN_KEYWORDS:
            if keyword in expr_lower:
                raise ValueError(f"Forbidden keyword detected: {keyword}")
        
        # 3. 检查是否只包含允许的字符
        # 允许：数字、小数点、运算符、括号、空格、数学函数名
        allowed_pattern = r'^[\d\s\+\-\*\/\%\^\(\)\.\,a-zA-Z_]+$'
        if not re.match(allowed_pattern, expr):
            raise ValueError("Expression contains invalid characters")
        
        # 4. 检查括号匹配
        if expr.count('(') != expr.count(')'):
            raise ValueError("Unmatched parentheses")
        
        # 5. 替换数学常量
        expr = expr.replace('pi', str(math.pi))
        expr = expr.replace('e', str(math.e))
        
        # 6. 使用受限的 eval 环境
        try:
            # 创建安全的命名空间
            safe_dict = {k: v for k, v in cls.SAFE_FUNCTIONS.items()}
            safe_dict['__builtins__'] = {}  # 禁用所有内置函数
            
            # 执行求值
            result = eval(expr, {"__builtins__": {}}, safe_dict)
            
            # 验证结果类型
            if not isinstance(result, (int, float)):
                raise ValueError(f"Invalid result type: {type(result)}")
            
            return float(result)
            
        except Exception as e:
            raise ValueError(f"Expression evaluation failed: {str(e)}")


class CalculatorTool(BaseTool):
    """
    计算器工具
    
    功能：
    - 执行数学计算
    - 支持基本运算：+、-、*、/、%、**
    - 支持数学函数：sin、cos、tan、log、sqrt 等
    - 支持数学常量：pi、e
    
    安全机制：
    - 使用白名单机制，只允许安全的运算
    - 禁止代码注入
    - 禁止系统调用
    """
    
    def __init__(self):
        """初始化计算器工具"""
        super().__init__(
            name="calculator",
            description="执行数学计算，支持基本运算、数学函数和常量"
        )
        self.timeout = 5  # 计算器执行很快，5 秒足够
        self.evaluator = SafeExpressionEvaluator()
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证参数
        
        Args:
            expression: 数学表达式
        
        Returns:
            bool: 参数是否有效
        
        Raises:
            ValueError: 参数无效
        """
        expression = kwargs.get('expression')
        
        if not expression:
            raise ValueError("Parameter 'expression' is required")
        
        if not isinstance(expression, str):
            raise ValueError("Parameter 'expression' must be a string")
        
        if len(expression) > 1000:
            raise ValueError("Expression too long (max 1000 characters)")
        
        return True
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行计算
        
        Args:
            expression: 数学表达式
        
        Returns:
            ToolResult: 计算结果
        """
        expression = kwargs.get('expression')
        
        try:
            # 安全求值
            result = self.evaluator.evaluate(expression)
            
            return ToolResult(
                success=True,
                output=result,
                metadata={
                    "expression": expression,
                    "result_type": type(result).__name__
                }
            )
            
        except ValueError as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Calculator tool error: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Calculation failed: {str(e)}"
            )
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 schema"""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如：2 + 2、sqrt(16)、sin(pi/2)"
                }
            },
            "required": ["expression"]
        }