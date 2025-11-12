"""
基于LangChain Embeddings自定义接口实现，兼容opanai的模型可使用
不兼容opanai的模型可以仿照修改 __init__， embed_query，embed_documents
支持异步方法：aembed_query 和 aembed_documents
"""

from typing import List
import asyncio
from openai import OpenAI, AsyncOpenAI
from langchain_core.embeddings import Embeddings


class CloudEmbeddings(Embeddings):
    """以阿里云百炼Embeddings封装类为示例，支持同步和异步方法"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "text-embedding-v4",
        **kwargs
    ):
        """
        初始化Embeddings
        
        Args:
            api_key (str): API Key
            base_url (str): API基础URL，默认为北京地域
            model (str): 使用的embedding模型，默认为text-embedding-v4
            **kwargs: 其他参数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
        # 创建同步OpenAI客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 创建异步OpenAI客户端
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def embed_query(self, text: str) -> List[float]:
        """
        对单个文本进行嵌入
        
        Args:
            text (str): 要嵌入的文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            # 提取嵌入向量
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            raise Exception(f"嵌入查询失败: {str(e)}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对多个文本进行嵌入
        
        Args:
            texts (List[str]): 要嵌入的文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            # 提取所有嵌入向量
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            raise Exception(f"嵌入文档失败: {str(e)}")
    
    async def aembed_query(self, text: str) -> List[float]:
        """
        异步对单个文本进行嵌入
        
        Args:
            text (str): 要嵌入的文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            response = await self.async_client.embeddings.create(
                model=self.model,
                input=text
            )
            
            # 提取嵌入向量
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            raise Exception(f"异步嵌入查询失败: {str(e)}")
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        异步对多个文本进行嵌入
        
        Args:
            texts (List[str]): 要嵌入的文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        try:
            response = await self.async_client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            # 提取所有嵌入向量
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            raise Exception(f"异步嵌入文档失败: {str(e)}")


async def test_async_embeddings():
    """测试异步嵌入方法"""
    try:
        # 使用示例
        api_key = ""  # 请替换为你的API Key
        
        # 创建embeddings实例
        embeddings = CloudEmbeddings(api_key=api_key)
        
        # 测试异步单个文本嵌入
        text = "衣服的质量杠杠的"
        result = await embeddings.aembed_query(text)
        print(f"异步单个文本嵌入结果长度: {len(result)}")
        print(f"前5个值: {result[:5]}")
        
        # 测试异步多个文本嵌入
        texts = ["衣服的质量很好", "这个产品很不错", "服务态度很好"]
        results = await embeddings.aembed_documents(texts)
        print(f"异步多个文本嵌入结果数量: {len(results)}")
        print(f"每个嵌入向量的长度: {len(results[0])}")
        
    except Exception as e:
        print(f"异步测试失败: {e}")


if __name__ == "__main__":
    # 测试同步代码
    try:
        # 使用示例
        api_key = ""  # 请替换为你的API Key
        
        # 创建embeddings实例
        embeddings = CloudEmbeddings(api_key=api_key)
        
        # 测试单个文本嵌入
        text = "衣服的质量杠杠的"
        result = embeddings.embed_query(text)
        print(f"同步单个文本嵌入结果长度: {len(result)}")
        print(f"前5个值: {result[:5]}")
        
        # 测试多个文本嵌入
        texts = ["衣服的质量很好", "这个产品很不错", "服务态度很好"]
        results = embeddings.embed_documents(texts)
        print(f"同步多个文本嵌入结果数量: {len(results)}")
        print(f"每个嵌入向量的长度: {len(results[0])}")
        
        # 运行异步测试
        print("\n--- 开始异步测试 ---")
        asyncio.run(test_async_embeddings())
        
    except Exception as e:
        print(f"测试失败: {e}")
