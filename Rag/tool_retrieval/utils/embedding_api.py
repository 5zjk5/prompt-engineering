import dashscope
import json
import os
from http import HTTPStatus
from typing import Dict, Any, List


class EmbeddingAPI:
    """
    多模态嵌入API封装类，用于调用dashscope的多模态嵌入模型
    """
    
    def __init__(self):
        """
        初始化EmbeddingAPI实例
        """
        self.model = os.getenv('EMBEDDING_MODEL', 'multimodal-embedding-v1')
        self.api_key = os.getenv('MODELSCOPE_API_KEY')
        
        if not self.api_key:
            raise ValueError("API密钥未提供，请设置MODELSCOPE_API_KEY环境变量或在初始化时传入api_key参数")
    
    async def get_embedding(self, text: str) -> Dict[str, Any]:
        """
        获取文本的嵌入向量
        
        Args:
            text: 要获取嵌入向量的文本
            
        Returns:
            包含嵌入向量和其他信息的字典
        """
        inputs = [{'text': text}]
        
        # 调用模型接口
        resp = dashscope.MultiModalEmbedding.call(
            model=self.model,
            input=inputs,
            api_key=self.api_key
        )
        
        # 根据您提供的返回结构处理响应
        if resp.status_code == HTTPStatus.OK:
            embedding_content = resp.output['embeddings'][0]['embedding']
            return embedding_content
        else:
            raise Exception(f'获取嵌入向量失败: {resp.status_code} {resp.message}')
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取文本的嵌入向量
        
        Args:
            texts: 要获取嵌入向量的文本列表
            
        Returns:
            包含嵌入向量和其他信息的字典列表
        """
        results = []
        for text in texts:
            result = await self.get_embedding(text)
            results.append(result)
        return results
