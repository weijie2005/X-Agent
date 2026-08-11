"""
Agentic RAG 模块

实现 Agent 自主判断是否检索、检索几轮、是否需要补充检索。
"""
import logging
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.agent.rag.crag_system import CRAGSystem

logger = logging.getLogger(__name__)
settings = get_settings()


class AgenticRAG:
    """
    Agentic RAG 系统
    
    Agent 自主控制检索过程。
    """
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base"
    ):
        """
        初始化 Agentic RAG
        
        Args:
            collection_name: 集合名称
        """
        self.crag_system = CRAGSystem(collection_name)
        
        # 初始化 LLM 用于决策
        self.llm = ChatOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL_NAME,
            temperature=0.0
        )
    
    def should_retrieve(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        判断是否需要检索
        
        Args:
            query: 查询文本
            conversation_history: 对话历史
        
        Returns:
            是否需要检索
        """
        # 使用 CRAG 的简单规则先判断
        if self.crag_system.check_need_retrieval(query, conversation_history):
            return True
        
        # 使用 LLM 判断
        prompt = f"""请判断以下查询是否需要从知识库中检索信息来回答。

查询: {query}

请只回答"是"或"否"，不要有其他内容。"""
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            return answer == "是"
            
        except Exception as e:
            logger.error(f"Failed to determine retrieval need: {e}")
            # 默认不检索
            return False
    
    def determine_retrieval_strategy(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        确定检索策略
        
        Args:
            query: 查询文本
            conversation_history: 对话历史
            filter_conditions: 过滤条件
        
        Returns:
            检索策略字典
        """
        # 先进行初始检索
        initial_results, initial_stats = self.crag_system.retrieve_with_validation(
            query,
            limit=5,
            filter_conditions=filter_conditions
        )
        
        # 判断检索轮数
        retrieval_rounds = self.crag_system.determine_retrieval_rounds(
            query,
            initial_results
        )
        
        # 判断是否需要补充检索
        need_supplement = self._check_need_supplement(query, initial_results)
        
        strategy = {
            "need_retrieval": len(initial_results) > 0,
            "retrieval_rounds": retrieval_rounds,
            "need_supplement": need_supplement,
            "initial_results": initial_results,
            "initial_stats": initial_stats
        }
        
        return strategy
    
    def _check_need_supplement(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> bool:
        """
        检查是否需要补充检索
        
        Args:
            query: 查询文本
            results: 检索结果
        
        Returns:
            是否需要补充检索
        """
        # 如果没有结果，需要补充
        if not results:
            return True
        
        # 如果结果质量不高，需要补充
        avg_score = sum(
            r.get('combined_score', r.get('score', 0))
            for r in results
        ) / len(results)
        
        if avg_score < 0.5:
            return True
        
        # 使用 LLM 判断
        prompt = f"""请判断以下检索结果是否足够回答查询。

查询: {query}

检索结果数量: {len(results)}
平均相关度: {avg_score:.2f}

请只回答"是"或"否"，不要有其他内容。"""
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            return answer == "否"
            
        except Exception as e:
            logger.error(f"Failed to check supplement need: {e}")
            return False
    
    def retrieve(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行检索
        
        Args:
            query: 查询文本
            conversation_history: 对话历史
            filter_conditions: 过滤条件
        
        Returns:
            检索结果字典
        """
        # 1. 判断是否需要检索
        if not self.should_retrieve(query, conversation_history):
            return {
                "need_retrieval": False,
                "results": [],
                "stats": {
                    "total_retrieved": 0,
                    "validated": 0,
                    "discarded": 0,
                    "retry_count": 0
                }
            }
        
        # 2. 确定检索策略
        strategy = self.determine_retrieval_strategy(query, conversation_history, filter_conditions)
        
        # 3. 执行多轮检索（如果需要）
        all_results = strategy["initial_results"]
        all_stats = strategy["initial_stats"]
        
        if strategy["retrieval_rounds"] > 1:
            for round_num in range(1, strategy["retrieval_rounds"]):
                # 降低阈值
                score_threshold = max(0.3, 0.5 - round_num * 0.1)
                
                # 检索
                results, stats = self.crag_system.retrieve_with_validation(
                    query,
                    limit=5,
                    score_threshold=score_threshold,
                    filter_conditions=filter_conditions
                )
                
                # 合并结果
                for result in results:
                    chunk_id = result.get('chunk_id')
                    if not any(r.get('chunk_id') == chunk_id for r in all_results):
                        all_results.append(result)
                
                # 更新统计
                all_stats["total_retrieved"] += stats["total_retrieved"]
                all_stats["validated"] += stats["validated"]
                all_stats["discarded"] += stats["discarded"]
                all_stats["retry_count"] += 1
        
        # 4. 补充检索（如果需要）
        if strategy["need_supplement"] and len(all_results) < 3:
            # 使用不同的查询方式
            supplement_query = self._generate_supplement_query(query)
            
            results, stats = self.crag_system.retrieve_with_validation(
                supplement_query,
                limit=3,
                score_threshold=0.4
            )
            
            # 合并结果
            for result in results:
                chunk_id = result.get('chunk_id')
                if not any(r.get('chunk_id') == chunk_id for r in all_results):
                    all_results.append(result)
            
            # 更新统计
            all_stats["total_retrieved"] += stats["total_retrieved"]
            all_stats["validated"] += stats["validated"]
            all_stats["discarded"] += stats["discarded"]
            all_stats["supplement_query"] = supplement_query
        
        return {
            "need_retrieval": True,
            "results": all_results[:10],  # 最多返回 10 个结果
            "stats": all_stats
        }
    
    def _generate_supplement_query(self, query: str) -> str:
        """
        生成补充查询
        
        Args:
            query: 原始查询
        
        Returns:
            补充查询
        """
        prompt = f"""请将以下查询改写为更通用的形式，用于补充检索。

原始查询: {query}

请只输出改写后的查询，不要有其他内容。"""
        
        try:
            response = self.llm.invoke(prompt)
            supplement_query = response.content.strip()
            
            return supplement_query
            
        except Exception as e:
            logger.error(f"Failed to generate supplement query: {e}")
            return query
    
    def format_context(
        self,
        results: List[Dict[str, Any]],
        max_length: int = 2000
    ) -> str:
        """
        格式化检索结果为上下文
        
        Args:
            results: 检索结果列表
            max_length: 最大长度
        
        Returns:
            格式化的上下文字符串
        """
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            score = result.get('combined_score', result.get('score', 0))
            
            part = f"[文档{i}] (相关度: {score:.2f})\n{content}\n\n"
            
            if current_length + len(part) > max_length:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        context = "".join(context_parts)
        
        return context.strip()