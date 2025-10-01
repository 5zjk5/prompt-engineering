import chromadb
import logging
import time
import os
import numpy as np
import jieba.posseg as pseg
from typing import Dict, Any, List
from utils.embedding_api import EmbeddingAPI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi


class RetrievalService:
    """
    检索服务类，提供多种检索方法
    """
    
    def __init__(self, db_path: str, logger: logging.Logger = None):
        """
        初始化检索服务
        
        Args:
            db_path: 数据库路径
            logger: 日志记录器
        """
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_api = EmbeddingAPI()
        self.logger = logger or logging.getLogger(__name__)
        
        # 获取或创建集合
        self.tool_vector_collection = self.client.get_or_create_collection(name="tool_vector")
        self.hypothetical_query_collection = self.client.get_or_create_collection(name="hypothetical_query")
        
        # 缓存目录
        self.cache_dir = os.path.join(os.path.dirname(db_path), "db/cache")
        self.logger.info(f'Cache dir: {self.cache_dir}')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def _get_document_collection(self, collection_name: str = None) -> List[Dict[str, Any]]:
        """
        获取文档集合
        
        Args:
            collection_name: 集合名称，可选值为 "tool_vector" 或 "hypothetical_query"，
                           如果为None，则返回两个集合的合并结果
        
        Returns:
            文档列表，每个文档包含id、content和metadata
        """
        all_docs = []
        
        # 获取tool_vector_collection的文档
        if collection_name is None or collection_name == "tool_vector":
            tool_results = self.tool_vector_collection.get(
                include=["documents", "metadatas"]
            )
            for i in range(len(tool_results['ids'])):
                all_docs.append({
                    'id': tool_results['ids'][i],
                    'content': tool_results['documents'][i],
                    'metadata': tool_results['metadatas'][i],
                    'collection': 'tool_vector'
                })
        
        # 获取hypothetical_query_collection的文档
        if collection_name is None or collection_name == "hypothetical_query":
            hypothetical_results = self.hypothetical_query_collection.get(
                include=["documents", "metadatas"]
            )
            for i in range(len(hypothetical_results['ids'])):
                all_docs.append({
                    'id': hypothetical_results['ids'][i],
                    'content': hypothetical_results['documents'][i],
                    'metadata': hypothetical_results['metadatas'][i],
                    'collection': 'hypothetical_query'
                })
        
        return all_docs

    def _tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词
        
        Args:
            text: 要分词的文本
            
        Returns:
            分词结果列表
        """
        # 使用jieba进行分词
        words = pseg.cut(text)
        # 过滤掉标点符号，只保留词语
        return [word.word for word in words if word.flag != 'x']

    def _deduplicate_results(self, results: List[Dict[str, Any]], n_results: int, score_key: str = 'score') -> List[Dict[str, Any]]:
        """
        根据工具名对检索结果进行去重
        
        Args:
            results: 检索结果列表
            n_results: 返回结果数量
            score_key: 分数字段名，默认为'score'
            
        Returns:
            去重后的结果列表
        """
        # 根据工具名去重
        unique_results = {}
        for result in results:
            tool_name = result['tool_id']
            if tool_name not in unique_results:
                unique_results[tool_name] = result
        
        # 按分数排序并取前n_results个去重后的结果
        return sorted(unique_results.values(), key=lambda x: x[score_key], reverse=True)[:n_results]

    async def dense_retrieval(self, query: str, n_results: int = 5, logger: logging.Logger = None) -> List[Dict[str, Any]]:
        log = logger or self.logger
        start_time = time.time()
        
        # 生成查询嵌入
        query_embedding = await self.embedding_api.get_embedding(query)
        
        # 从tool_vector_collection执行向量检索
        tool_results = self.tool_vector_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # 从hypothetical_query_collection执行向量检索
        hypothetical_results = self.hypothetical_query_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # 合并结果
        all_results = []
        
        # 处理tool_vector_collection的结果
        for ids, distances, metadatas, documents in zip(tool_results['ids'], tool_results['distances'], tool_results['metadatas'], tool_results['documents']):
            for i in range(len(ids)):
                # 余弦相似度范围：-1到1，值越大表示越相似
                # 实际应用中通常在0到1之间
                similarity = 1 - distances[i]
                all_results.append({
                    'tool_id': ids[i],
                    'similarity': similarity,
                    'metadata': metadatas[i],
                    'document': documents[i],
                    'collection': 'tool_vector',
                    'score_type': 'cosine_similarity'
                })
        
        # 处理hypothetical_query_collection的结果
        for ids, distances, metadatas, documents in zip(hypothetical_results['ids'], hypothetical_results['distances'], hypothetical_results['metadatas'], hypothetical_results['documents']):
            for i in range(len(ids)):
                # 余弦相似度范围：-1到1，值越大表示越相似
                # 实际应用中通常在0到1之间
                similarity = 1 - distances[i]
                all_results.append({
                    'tool_id': ids[i],
                    'similarity': similarity,
                    'metadata': metadatas[i],
                    'document': documents[i],
                    'collection': 'hypothetical_query',
                    'score_type': 'cosine_similarity'
                })
        
        # 按相似度排序
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 根据工具名去重
        formatted_results = self._deduplicate_results(all_results, n_results, 'similarity')
        
        log.info(f"稠密检索耗时: {time.time() - start_time:.2f}s")
        return formatted_results

    async def sparse_retrieval_bm25(self, query: str, n_results: int = 5, logger: logging.Logger = None) -> List[Dict[str, Any]]:
        log = logger or self.logger
        start_time = time.time()
        
        # 获取两个集合的文档
        docs = await self._get_document_collection()
        
        # 对文档进行分词
        tokenized_docs = [self._tokenize(doc['content']) for doc in docs]
        
        # 创建BM25索引
        self.bm25 = BM25Okapi(tokenized_docs)
        
        # 执行BM25检索
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[-n_results:][::-1]
        
        # 格式化结果
        results = [{
            'tool_id': docs[i]['id'],
            'score': float(scores[i]),  # BM25分数范围：0到正无穷，值越大表示越相关
            'metadata': docs[i]['metadata'],
            'document': docs[i]['content'],
            'collection': docs[i]['collection'],  # 添加集合来源信息
            'score_type': 'bm25',
            'normalized_score': float(scores[i]) / (max(scores) + 1e-6)  # 添加归一化分数，用于混合检索
        } for i in top_indices]
        
        # 根据工具名去重
        formatted_results = self._deduplicate_results(results, n_results, 'score')
        
        log.info(f"BM25检索耗时: {time.time() - start_time:.2f}s")
        return formatted_results

    async def hybrid_retrieval(self, query: str, n_results: int = 5, logger: logging.Logger = None, 
                           methods: List[str] = None, weights: Dict[str, float] = None,
                           strategy: str = "rank_fusion") -> List[Dict[str, Any]]:
        """
        混合检索方法，结合多种检索方法的结果
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            logger: 日志记录器
            methods: 要使用的检索方法列表，默认为['dense', 'sparse', 'keyword']
            weights: 各检索方法的权重，默认为None（根据策略自动计算）
            strategy: 混合策略，可选值为"adaptive"（自适应）、"rank_fusion"（排序融合）、"weighted"（加权平均）
            
        Returns:
            检索结果列表
        """
        log = logger or self.logger
        start_time = time.time()
        
        # 设置默认检索方法
        if methods is None:
            methods = ['dense', 'sparse', 'keyword']
        
        # 根据策略设置权重
        if weights is None:
            if strategy == "adaptive":
                # 自适应策略：根据查询长度和内容动态调整权重
                query_length = len(query)
                if query_length < 10:  # 短查询，关键词匹配更重要
                    weights = {'dense': 0.3, 'sparse': 0.4, 'keyword': 0.3}
                elif query_length < 30:  # 中等查询，平衡各方法
                    weights = {'dense': 0.4, 'sparse': 0.3, 'keyword': 0.3}
                else:  # 长查询，语义匹配更重要
                    weights = {'dense': 0.5, 'sparse': 0.2, 'keyword': 0.3}
            elif strategy == "rank_fusion":
                # 排序融合策略：使用倒数排名融合，不需要权重
                weights = None
            else:  # weighted策略
                weights = {'dense': 0.4, 'sparse': 0.3, 'keyword': 0.3}
        
        # 验证权重总和为1（如果不是rank_fusion策略）
        if weights is not None:
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 1e-6:
                log.warning(f"权重总和不为1 ({total_weight})，将进行归一化")
                weights = {k: v / total_weight for k, v in weights.items()}
        
        # 串行执行各检索方法
        all_results = {}
        method_times = {}
        
        for method in methods:
            method_start = time.time()
            if method == 'dense':
                results = await self.dense_retrieval(query, n_results * 2, logger)  # 获取更多结果以提高混合质量
            elif method == 'sparse':
                results = await self.sparse_retrieval_bm25(query, n_results * 2, logger)
            elif method == 'keyword':
                results = await self.keyword_search(query, n_results * 2, logger)
            else:
                log.warning(f"不支持的检索方法: {method}，跳过")
                continue
            
            method_times[method] = time.time() - method_start
            all_results[method] = results
        
        # 合并结果并去重
        merged_results = {}
        
        for method, results in all_results.items():
            for item in results:
                tool_id = item['tool_id']
                
                # 如果工具ID已存在，则更新分数
                if tool_id in merged_results:
                    # 使用各方法的分数
                    if method == 'dense':
                        # dense_retrieval的similarity已经在0-1范围
                        normalized_score = item['similarity']
                    elif method == 'sparse':
                        # BM25分数使用预先计算的归一化分数
                        normalized_score = item['normalized_score']
                    elif method == 'keyword':
                        # keyword_search的score已经在0-1范围
                        normalized_score = item['score']
                    
                    # 更新合并结果中的分数
                    if 'scores' not in merged_results[tool_id]:
                        merged_results[tool_id]['scores'] = {}
                    
                    merged_results[tool_id]['scores'][method] = normalized_score
                    merged_results[tool_id]['raw_scores'][method] = item.get('similarity', item.get('score', 0))
                else:
                    # 创建新条目
                    merged_item = {
                        'tool_id': tool_id,
                        'metadata': item['metadata'],
                        'document': item['document'],
                        'collection': item['collection'],
                        'scores': {},
                        'raw_scores': {}
                    }
                    
                    # 使用各方法的分数
                    if method == 'dense':
                        normalized_score = item['similarity']
                        raw_score = item['similarity']
                    elif method == 'sparse':
                        normalized_score = item['normalized_score']
                        raw_score = item['score']
                    elif method == 'keyword':
                        normalized_score = item['score']
                        raw_score = item['score']
                    
                    merged_item['scores'][method] = normalized_score
                    merged_item['raw_scores'][method] = raw_score
                    merged_results[tool_id] = merged_item
        
        # 根据策略计算最终分数
        if strategy == "rank_fusion":
            # 倒数排名融合（Reciprocal Rank Fusion）
            for tool_id, item in merged_results.items():
                rrf_score = 0.0  # 确保初始化为浮点数
                for method, scores in all_results.items():
                    # 找到该工具在各方法中的排名
                    rank = 1
                    found = False
                    for result in scores:
                        if result['tool_id'] == tool_id:
                            rrf_score += 1.0 / (rank + 60)  # 60是一个平滑参数，避免排名靠后的结果分数过低
                            found = True
                            break
                        rank += 1
                    if not found:
                        # 如果该方法没有返回该工具，给它一个较低的分数
                        rrf_score += 1.0 / (len(scores) + 60 + 1)
                # 确保rrf_score是实数
                if isinstance(rrf_score, complex):
                    rrf_score = rrf_score.real
                item['weighted_score'] = float(rrf_score)
        else:
            # 加权平均策略（包括adaptive策略）
            for tool_id, item in merged_results.items():
                weighted_score = 0.0  # 确保初始化为浮点数
                # 计算各方法的加权分数
                for method, score in item['scores'].items():
                    if method in weights:
                        # 确保score是实数
                        if isinstance(score, complex):
                            score = score.real
                        
                        # 对分数应用非线性变换，增强高分结果的权重
                        if strategy == "adaptive":
                            # 自适应策略：对高分结果应用更强的权重
                            enhanced_score = float(score) ** 1.5
                        else:
                            enhanced_score = float(score)
                        weighted_score += enhanced_score * weights[method]
                
                # 确保weighted_score是实数
                if isinstance(weighted_score, complex):
                    weighted_score = weighted_score.real
                item['weighted_score'] = float(weighted_score)
        
        # 使用公共去重函数进行最终去重
        # 将merged_results转换为适合_deduplicate_results函数的格式
        dedup_input = []
        for tool_id, item in merged_results.items():
            dedup_item = {
                'tool_id': tool_id,
                'score': item['weighted_score'],  # 使用加权分数作为去重依据
                'metadata': item['metadata'],
                'document': item['document'],
                'collection': item['collection'],
                'scores': item['scores'],
                'raw_scores': item['raw_scores']
            }
            dedup_input.append(dedup_item)
        
        # 使用公共去重函数
        dedup_results = self._deduplicate_results(dedup_input, n_results, 'score')
        
        # 格式化最终结果
        formatted_results = []
        for item in dedup_results:
            formatted_item = {
                'tool_id': item['tool_id'],
                'score': item['score'],  # 使用加权分数作为最终分数
                'metadata': item['metadata'],
                'document': item['document'],
                'collection': item['collection'],
                'score_type': 'hybrid',
                'method_scores': item['scores'],  # 各方法的标准化分数
                'raw_method_scores': item['raw_scores']  # 各方法的原始分数
            }
            formatted_results.append(formatted_item)
        
        # 记录各方法耗时和策略信息
        for method, t in method_times.items():
            log.info(f"{method}检索耗时: {t:.2f}s")
        log.info(f"混合检索策略: {strategy}")
        if weights:
            log.info(f"混合检索权重: {weights}")
        log.info(f"混合检索总耗时: {time.time() - start_time:.2f}s")
        
        return formatted_results

    async def keyword_search(self, query: str, n_results: int = 5, logger: logging.Logger = None) -> List[Dict[str, Any]]:
        """
        基于TF-IDF的关键词检索
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            logger: 日志记录器
            
        Returns:
            检索结果列表
        """
        log = logger or self.logger
        start_time = time.time()
        
        # 获取两个集合的文档
        docs = await self._get_document_collection()
        
        # 提取文档内容
        doc_contents = [doc['content'] for doc in docs]
        
        # 创建TF-IDF向量化器
        # 使用jieba分词作为tokenizer
        vectorizer = TfidfVectorizer(tokenizer=self._tokenize)
        
        # 对文档进行向量化
        tfidf_matrix = vectorizer.fit_transform(doc_contents)
        
        # 对查询进行向量化
        query_tfidf = vectorizer.transform([query])
        
        # 计算查询与文档的余弦相似度
        similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
        
        # 获取相似度最高的n_results个文档的索引
        top_indices = np.argsort(similarities)[-n_results:][::-1]
        
        # 格式化结果
        results = [{
            'tool_id': docs[i]['id'],
            'score': float(similarities[i]),  # TF-IDF余弦相似度，范围：0到1，值越大表示越相关
            'metadata': docs[i]['metadata'],
            'document': docs[i]['content'],
            'collection': docs[i]['collection'],  # 添加集合来源信息
            'score_type': 'tfidf'
        } for i in top_indices]
        
        # 根据工具名去重
        formatted_results = self._deduplicate_results(results, n_results, 'score')
        
        log.info(f"TF-IDF关键词检索耗时: {time.time() - start_time:.2f}s")
        return formatted_results


async def retrieval_tool_func(db_path: str, query: str, method: str = "hybrid", n_results: int = 5, logger: logging.Logger = None) -> List[Dict[str, Any]]:
    """
    根据查询检索工具
    
    Args:
        db_path: 数据库路径
        query: 查询文本
        method: 检索方法，可选值为 "dense", "sparse", "hybrid", "semantic", "keyword"
        n_results: 返回结果数量
        logger: 日志记录器
        
    Returns:
        检索结果列表
    """
    # 使用传入的logger或默认logger
    log = logger or logging.getLogger(__name__)
    
    # 记录开始时间
    start_time = time.time()
    
    # 初始化检索服务
    init_start = time.time()
    retrieval_service = RetrievalService(db_path, logger)
    init_time = time.time() - init_start
    log.info(f"初始化检索服务耗时: {init_time:.4f}秒")
    
    # 根据方法调用相应的检索函数
    retrieval_start = time.time()
    if method == "dense":
        results = await retrieval_service.dense_retrieval(query, n_results, logger)
    elif method == "sparse":
        results = await retrieval_service.sparse_retrieval_bm25(query, n_results, logger)
    elif method == "hybrid":
        results = await retrieval_service.hybrid_retrieval(query, n_results, logger)
    elif method == "keyword":
        results = await retrieval_service.keyword_search(query, n_results, logger)
    else:
        raise ValueError(f"不支持的检索方法: {method}，请选择 'dense', 'sparse', 'hybrid', 'semantic', 'keyword' 中的一种")
    
    retrieval_time = time.time() - retrieval_start
    total_time = time.time() - start_time
    log.info(f"检索操作耗时: {retrieval_time:.4f}秒")
    log.info(f"retrieval_tool总耗时: {total_time:.4f}秒")
    
    return results
