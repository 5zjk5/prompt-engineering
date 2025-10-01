import json
import chromadb
from utils.embedding_api import EmbeddingAPI
from typing import Dict, Any
from fastapi import HTTPException


async def update_tool_to_db(db_path: str, tool_json: Dict[str, Any]) -> None:
    """
    接收db路径及工具json，把name作为id，更新数据库中的工具信息和假设性问题
    
    Args:
        db_path: 数据库路径
        tool_json: 工具JSON数据

    Raises:
        HTTPException: 如果ID不存在或更新过程中发生错误
    """
    # 提取工具名称作为ID
    tool_id = tool_json["name"]
        
    # 连接到Chroma数据库
    client = chromadb.PersistentClient(path=db_path)
        
    # 获取tool_vector集合
    tool_vector_collection = client.get_or_create_collection(name="tool_vector")

    # 获取hypothetical_query集合
    hypothetical_query_collection = client.get_or_create_collection(name="hypothetical_query")
    
    # 检查ID是否存在
    existing_documents = tool_vector_collection.get(ids=[tool_id])
    if not existing_documents or not existing_documents['ids']:
        raise HTTPException(status_code=404, detail=f"ID '{tool_id}' not found in the tool_vector collection.")
    
    # 先删除工具向量的旧数据
    tool_vector_collection.delete(ids=[tool_id])
    
    # 删除假设性问题的旧数据
    hypothetical_query_collection.delete(ids=[tool_id])
        
    # 将整个JSON转换为字符串用于向量化
    tool_content = json.dumps(tool_json, ensure_ascii=False, separators=(',', ':'))
        
    # 初始化向量模型
    embedding_api = EmbeddingAPI()
        
    # 获取工具内容的向量表示
    embedding_result = await embedding_api.get_embedding(tool_content)
        
    # 添加新数据到集合中
    tool_vector_collection.add(
        documents=[tool_content],
        embeddings=[embedding_result],
        ids=[tool_id]
    )
