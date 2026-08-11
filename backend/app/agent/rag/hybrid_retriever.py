"""
RAG 混合检索模块

实现语义检索、关键词检索、元数据过滤和重排。
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from app.agent.rag.embedding_engine import RAGIndexer

logger = logging.getLogger(__name__)


class KeywordSearcher:
    """
    关键词检索器
    
    实现基于关键词的检索。
    """
    
    def __init__(self):
        """初始化关键词检索器"""
        # 停用词列表
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就',
            '不', '人', '都', '一', '一个', '上', '也', '很',
            '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这', 'the', 'a', 'an', 'is',
            'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may',
            'might', 'must', 'shall', 'can', 'need',
            'to', 'of', 'in', 'for', 'on', 'with',
            'at', 'by', 'from', 'as', 'into', 'through'
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本内容
        
        Returns:
            关键词列表
        """
        # 分词（简单实现：按空格和标点符号分词）
        words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
        
        # 过滤停用词
        keywords = [
            word for word in words
            if word not in self.stop_words and len(word) > 1
        ]
        
        return keywords
    
    def calculate_keyword_score(
        self,
        query_keywords: List[str],
        doc_keywords: List[str]
    ) -> float:
        """
        计算关键词匹配分数
        
        Args:
            query_keywords: 查询关键词
            doc_keywords: 文档关键词
        
        Returns:
            匹配分数（0-1）
        """
        if not query_keywords or not doc_keywords:
            return 0.0
        
        # 统计关键词频率
        query_counter = Counter(query_keywords)
        doc_counter = Counter(doc_keywords)
        
        # 计算交集
        common_keywords = set(query_counter.keys()) & set(doc_counter.keys())
        
        if not common_keywords:
            return 0.0
        
        # 计算分数
        score = sum(
            min(query_counter[kw], doc_counter[kw])
            for kw in common_keywords
        )
        
        # 归一化
        max_score = sum(query_counter.values())
        
        return score / max_score if max_score > 0 else 0.0


class ResultReranker:
    """
    结果重排器
    
    对检索结果进行重排，提高相关性。
    """
    
    def __init__(self, semantic_weight: float = 0.6, keyword_weight: float = 0.4):
        """
        初始化重排器
        
        Args:
            semantic_weight: 语义检索权重
            keyword_weight: 关键词检索权重
        """
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
    
    def rerank(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        重排结果
        
        Args:
            semantic_results: 语义检索结果
            keyword_scores: 关键词分数字典
        
        Returns:
            重排后的结果列表
        """
        reranked_results = []
        
        for result in semantic_results:
            chunk_id = result.get('chunk_id', '')
            
            # 获取分数
            semantic_score = result.get('score', 0.0)
            keyword_score = keyword_scores.get(chunk_id, 0.0)
            
            # 计算综合分数
            combined_score = (
                self.semantic_weight * semantic_score +
                self.keyword_weight * keyword_score
            )
            
            # 更新结果
            reranked_result = result.copy()
            reranked_result['semantic_score'] = semantic_score
            reranked_result['keyword_score'] = keyword_score
            reranked_result['combined_score'] = combined_score
            
            reranked_results.append(reranked_result)
        
        # 按综合分数排序
        reranked_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return reranked_results


class HybridRetriever:
    """
    混合检索器
    
    结合语义检索、关键词检索、元数据过滤和重排。
    """
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base",
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ):
        """
        初始化混合检索器
        
        Args:
            collection_name: 集合名称
            semantic_weight: 语义检索权重
            keyword_weight: 关键词检索权重
        """
        self.rag_indexer = RAGIndexer(collection_name)
        self.keyword_searcher = KeywordSearcher()
        self.reranker = ResultReranker(semantic_weight, keyword_weight)
    
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.2,
        filter_conditions: Optional[Dict[str, Any]] = None,
        enable_rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query: 查询文本
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filter_conditions: 过滤条件
            enable_rerank: 是否启用重排
        
        Returns:
            检索结果列表
        """
        try:
            # 1. 语义检索
            semantic_results = self.rag_indexer.search_similar(
                query,
                limit=limit * 2,  # 获取更多结果用于重排
                score_threshold=score_threshold,
                filter_conditions=filter_conditions
            )
            
            if not semantic_results:
                return []
            
            # 2. 关键词检索
            query_keywords = self.keyword_searcher.extract_keywords(query)
            
            keyword_scores = {}
            for result in semantic_results:
                doc_content = result.get('content', '')
                doc_keywords = self.keyword_searcher.extract_keywords(doc_content)
                
                keyword_score = self.keyword_searcher.calculate_keyword_score(
                    query_keywords,
                    doc_keywords
                )
                
                chunk_id = result.get('chunk_id', '')
                keyword_scores[chunk_id] = keyword_score
            
            # 3. 重排
            if enable_rerank:
                reranked_results = self.reranker.rerank(
                    semantic_results,
                    keyword_scores
                )
            else:
                reranked_results = semantic_results
            
            # 4. 限制结果数量
            final_results = reranked_results[:limit]
            
            logger.info(
                f"Retrieved {len(final_results)} results "
                f"(semantic: {len(semantic_results)}, reranked: {enable_rerank})"
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve: {e}")
            raise