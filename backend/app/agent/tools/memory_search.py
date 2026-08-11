"""
记忆搜索工具

搜索 Agent 的长期记忆中的相关信息。
"""
import logging
from typing import Dict, Any, Optional, List

from app.agent.tools.base import BaseTool, ToolResult
from app.agent.memory.memory_system import MemorySystem

logger = logging.getLogger(__name__)


class MemorySearchTool(BaseTool):
    """
    记忆搜索工具
    
    功能：
    - 搜索长期结构化记忆（PostgreSQL）
    - 搜索长期语义记忆（Qdrant）
    - 返回相关的历史对话和知识
    
    安全机制：
    - 只能搜索当前会话或用户授权的记忆
    - 结果数量限制
    """
    
    # 最大搜索结果数量
    MAX_RESULTS = 10
    
    def __init__(self):
        """初始化记忆搜索工具"""
        super().__init__(
            name="memory_search",
            description="搜索 Agent 的长期记忆，查找相关的历史对话和知识"
        )
        self.timeout = 10
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证参数
        
        Args:
            query: 搜索查询
            session_id: 会话 ID（可选）
            user_id: 用户 ID（可选）
            max_results: 最大结果数（可选）
        
        Returns:
            bool: 参数是否有效
        
        Raises:
            ValueError: 参数无效
        """
        query = kwargs.get('query')
        
        if not query:
            raise ValueError("Parameter 'query' is required")
        
        if not isinstance(query, str):
            raise ValueError("Parameter 'query' must be a string")
        
        if len(query) > 500:
            raise ValueError("Query too long (max 500 characters)")
        
        # 检查 max_results
        max_results = kwargs.get('max_results', 5)
        if not isinstance(max_results, int) or max_results < 1 or max_results > self.MAX_RESULTS:
            raise ValueError(f"max_results must be between 1 and {self.MAX_RESULTS}")
        
        return True
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行记忆搜索
        
        Args:
            query: 搜索查询
            session_id: 会话 ID（可选）
            user_id: 用户 ID（可选）
            max_results: 最大结果数
        
        Returns:
            ToolResult: 搜索结果
        """
        query = kwargs.get('query')
        session_id = kwargs.get('session_id', 'default')
        user_id = kwargs.get('user_id')
        max_results = kwargs.get('max_results', 5)
        
        try:
            # 初始化记忆系统
            memory = MemorySystem(
                session_id=session_id,
                user_id=user_id
            )
            
            # 搜索长期语义记忆（向量搜索）
            semantic_results = await memory.search_long_term_semantic_memory(
                query=query,
                limit=max_results
            )
            
            # 搜索长期结构化记忆（数据库搜索）
            structured_results = await memory.search_long_term_structured_memory(
                query=query,
                limit=max_results
            )
            
            # 合并结果
            all_results = []
            
            # 添加语义搜索结果
            for result in semantic_results:
                all_results.append({
                    "type": "semantic",
                    "content": result.get('content', ''),
                    "score": result.get('score', 0),
                    "metadata": result.get('metadata', {})
                })
            
            # 添加结构化搜索结果
            for result in structured_results:
                all_results.append({
                    "type": "structured",
                    "content": result.get('content', ''),
                    "metadata": result.get('metadata', {})
                })
            
            # 按相关性排序（如果有 score）
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # 限制结果数量
            all_results = all_results[:max_results]
            
            return ToolResult(
                success=True,
                output={
                    "query": query,
                    "results": all_results,
                    "total_results": len(all_results),
                    "semantic_count": len(semantic_results),
                    "structured_count": len(structured_results)
                },
                metadata={
                    "session_id": session_id,
                    "user_id": user_id,
                    "max_results": max_results
                }
            )
            
        except Exception as e:
            logger.error(f"Memory search tool error: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Memory search failed: {str(e)}"
            )
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询关键词"
                },
                "session_id": {
                    "type": "string",
                    "description": "会话 ID（可选）"
                },
                "user_id": {
                    "type": "string",
                    "description": "用户 ID（可选）"
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回的最大结果数",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }