"""
CRAG 纠错模块

实现检索结果有效性校验、无效结果丢弃、二次补搜。
"""
import logging
from typing import List, Dict, Any, Optional
import re

from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.agent.rag.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)
settings = get_settings()


class RetrievalValidator:
    """
    检索结果验证器
    
    验证检索结果的有效性。
    """
    
    def __init__(self):
        """初始化验证器"""
        # 初始化 LLM 用于验证
        self.llm = ChatOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL_NAME,
            temperature=0.0
        )
    
    def validate_relevance(
        self,
        query: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        验证结果相关性
        
        Args:
            query: 查询文本
            result: 检索结果
        
        Returns:
            是否相关
        """
        content = result.get('content', '')
        score = result.get('combined_score', result.get('score', 0))
        
        # 简单规则：分数阈值（降低到0.2）
        if score < 0.2:
            return False
        
        # 关键词匹配（改进版）
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 提取英文单词
        query_words = set(re.findall(r'\b[a-z]+\b', query_lower))
        content_words = set(re.findall(r'\b[a-z]+\b', content_lower))
        
        # 至少有一个英文单词匹配
        if query_words & content_words:
            return True
        
        # 提取中文字符（单字匹配）
        query_cn_chars = set(re.findall(r'[\u4e00-\u9fff]', query))
        content_cn_chars = set(re.findall(r'[\u4e00-\u9fff]', content))
        
        # 至少有2个中文字符匹配
        if len(query_cn_chars & content_cn_chars) >= 2:
            return True
        
        # 如果分数足够高，也认为相关
        return score >= 0.4
    
    def validate_quality(self, result: Dict[str, Any]) -> bool:
        """
        验证结果质量
        
        Args:
            result: 检索结果
        
        Returns:
            是否高质量
        """
        content = result.get('content', '')
        
        # 检查内容长度
        if len(content) < 10:
            return False
        
        # 检查内容完整性
        if content.endswith('...') or content.endswith('…'):
            return False
        
        # 检查内容是否有意义
        # 简单规则：至少包含一些字母或汉字
        if not re.search(r'[a-zA-Z\u4e00-\u9fff]', content):
            return False
        
        return True
    
    def validate_with_llm(
        self,
        query: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        使用 LLM 验证结果
        
        Args:
            query: 查询文本
            result: 检索结果
        
        Returns:
            是否相关
        """
        content = result.get('content', '')
        
        prompt = f"""请判断以下文档片段是否与查询相关。

查询: {query}

文档片段: {content}

请只回答"是"或"否"，不要有其他内容。"""
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            return answer == "是"
            
        except Exception as e:
            logger.error(f"Failed to validate with LLM: {e}")
            # 如果 LLM 验证失败，默认通过
            return True


class CRAGSystem:
    """
    CRAG 纠错系统
    
    实现检索结果有效性校验、无效结果丢弃、二次补搜。
    """
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base",
        max_retry: int = 2
    ):
        """
        初始化 CRAG 系统
        
        Args:
            collection_name: 集合名称
            max_retry: 最大重试次数
        """
        self.hybrid_retriever = HybridRetriever(collection_name)
        self.validator = RetrievalValidator()
        self.max_retry = max_retry
    
    def retrieve_with_validation(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.2,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        带验证的检索
        
        Args:
            query: 查询文本
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filter_conditions: 过滤条件
        
        Returns:
            (检索结果列表, 统计信息字典)
        """
        stats = {
            "total_retrieved": 0,
            "validated": 0,
            "discarded": 0,
            "retry_count": 0
        }
        
        all_results = []
        retry_count = 0
        current_limit = limit
        
        while retry_count <= self.max_retry and len(all_results) < limit:
            # 检索
            results = self.hybrid_retriever.retrieve(
                query,
                limit=current_limit,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions
            )
            
            stats["total_retrieved"] += len(results)
            
            # 验证结果
            for result in results:
                # 检查是否已经存在
                chunk_id = result.get('chunk_id')
                if any(r.get('chunk_id') == chunk_id for r in all_results):
                    continue
                
                # 验证相关性和质量
                is_relevant = self.validator.validate_relevance(query, result)
                is_quality = self.validator.validate_quality(result)
                
                if is_relevant and is_quality:
                    all_results.append(result)
                    stats["validated"] += 1
                else:
                    stats["discarded"] += 1
                    logger.info(
                        f"Discarded result: "
                        f"relevant={is_relevant}, quality={is_quality}"
                    )
            
            # 如果结果不足，尝试二次检索
            if len(all_results) < limit and retry_count < self.max_retry:
                retry_count += 1
                stats["retry_count"] = retry_count
                
                # 降低阈值，增加检索数量
                score_threshold = max(0.3, score_threshold - 0.1)
                current_limit = limit * 2
                
                logger.info(
                    f"Retry {retry_count}: "
                    f"threshold={score_threshold}, limit={current_limit}"
                )
            else:
                break
        
        # 限制最终结果数量
        final_results = all_results[:limit]
        
        logger.info(
            f"CRAG retrieval completed: "
            f"{len(final_results)} results, stats={stats}"
        )
        
        return final_results, stats
    
    def check_need_retrieval(
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
        # 简单规则：包含特定关键词
        retrieval_keywords = [
            '文档', '文件', '资料', '知识库', '库中',
            '查找', '搜索', '检索', '查询', '找到',
            'document', 'file', 'knowledge', 'search',
            'find', 'retrieve', 'query'
        ]
        
        query_lower = query.lower()
        for keyword in retrieval_keywords:
            if keyword in query_lower:
                return True
        
        # 检查是否是问题
        question_patterns = [
            r'什么是', r'如何', r'怎么', r'为什么',
            r'哪些', r'有没有', r'能否', r'可以',
            r'what', r'how', r'why', r'which', r'can'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def determine_retrieval_rounds(
        self,
        query: str,
        initial_results: List[Dict[str, Any]]
    ) -> int:
        """
        判断需要几轮检索
        
        Args:
            query: 查询文本
            initial_results: 初始检索结果
        
        Returns:
            检索轮数
        """
        # 如果初始结果质量很高，不需要多轮检索
        if not initial_results:
            return 2
        
        # 计算平均分数
        avg_score = sum(
            r.get('combined_score', r.get('score', 0))
            for r in initial_results
        ) / len(initial_results)
        
        if avg_score >= 0.7:
            return 1
        elif avg_score >= 0.5:
            return 2
        else:
            return 3


from typing import Tuple