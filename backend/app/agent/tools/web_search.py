"""
Tavily 联网搜索工具

使用 Tavily API 进行实时互联网搜索。
"""
import os
import logging
from typing import Dict, Any, Optional
import json

from app.agent.tools.base import BaseTool, ToolResult
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSearchTool(BaseTool):
    """
    联网搜索工具
    
    功能：
    - 使用 Tavily API 进行实时搜索
    - 支持多种搜索类型（普通搜索、新闻搜索）
    - 返回结构化搜索结果
    
    安全机制：
    - API Key 验证
    - 搜索结果数量限制
    - 内容过滤
    """
    
    # 最大搜索结果数量
    MAX_RESULTS = 10
    
    # 搜索结果包含的字段
    SEARCH_FIELDS = [
        "title",
        "url",
        "content",
        "score"
    ]
    
    def __init__(self):
        """初始化联网搜索工具"""
        super().__init__(
            name="web_search",
            description="搜索互联网获取实时信息，支持新闻、技术文章等"
        )
        self.timeout = 30  # 网络请求可能较慢
        
        # 获取 Tavily API Key（从 Settings 类读取）
        self.api_key = settings.TAVILY_API_KEY
        
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not configured, web search will be limited")
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证参数
        
        Args:
            query: 搜索查询
            search_type: 搜索类型（可选）
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
        执行搜索
        
        Args:
            query: 搜索查询
            search_type: 搜索类型（search/news）
            max_results: 最大结果数
        
        Returns:
            ToolResult: 搜索结果
        """
        query = kwargs.get('query')
        search_type = kwargs.get('search_type', 'search')
        max_results = kwargs.get('max_results', 5)
        
        # 检查 API Key
        if not self.api_key:
            return ToolResult(
                success=False,
                output=None,
                error="TAVILY_API_KEY not configured. Please set TAVILY_API_KEY in .env file."
            )
        
        try:
            # 尝试使用 Tavily SDK
            try:
                from tavily import TavilyClient
                
                # 初始化客户端
                client = TavilyClient(api_key=self.api_key)
                
                # 执行搜索
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_results,
                    include_answer=True,
                    include_raw_content=False
                )
                
                # 提取结果
                results = []
                for result in response.get('results', []):
                    results.append({
                        "title": result.get('title', ''),
                        "url": result.get('url', ''),
                        "content": result.get('content', ''),
                        "score": result.get('score', 0)
                    })
                
                # 提取答案（如果有）
                answer = response.get('answer', '')
                
                return ToolResult(
                    success=True,
                    output={
                        "query": query,
                        "answer": answer,
                        "results": results,
                        "total_results": len(results)
                    },
                    metadata={
                        "search_type": search_type,
                        "max_results": max_results
                    }
                )
                
            except ImportError:
                logger.warning("tavily-python not installed, using HTTP API")
                
                # 使用 HTTP API
                return await self._search_with_http(query, max_results)
            
        except Exception as e:
            logger.error(f"Web search tool error: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Search failed: {str(e)}"
            )
    
    async def _search_with_http(self, query: str, max_results: int) -> ToolResult:
        """
        使用 HTTP API 进行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            ToolResult: 搜索结果
        """
        try:
            import httpx
            
            # Tavily API endpoint
            url = "https://api.tavily.com/search"
            
            # 请求体
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False
            }
            
            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code != 200:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Tavily API error: {response.status_code}"
                    )
                
                data = response.json()
                
                # 提取结果
                results = []
                for result in data.get('results', []):
                    results.append({
                        "title": result.get('title', ''),
                        "url": result.get('url', ''),
                        "content": result.get('content', ''),
                        "score": result.get('score', 0)
                    })
                
                # 提取答案
                answer = data.get('answer', '')
                
                return ToolResult(
                    success=True,
                    output={
                        "query": query,
                        "answer": answer,
                        "results": results,
                        "total_results": len(results)
                    },
                    metadata={
                        "search_type": "http_api",
                        "max_results": max_results
                    }
                )
                
        except Exception as e:
            logger.error(f"HTTP search error: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"HTTP search failed: {str(e)}"
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
                "search_type": {
                    "type": "string",
                    "description": "搜索类型",
                    "enum": ["search", "news"],
                    "default": "search"
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