import chromadb
from fastapi import HTTPException


async def delete_tool_from_db(db_path: str, tool_name: str) -> None:
    """
    根据工具名称从数据库中删除工具
    
    Args:
        db_path: 数据库路径
        tool_name: 工具名称（ID）

    Raises:
        HTTPException: 如果ID不存在或删除过程中发生错误
    """
    # 连接到Chroma数据库
    client = chromadb.PersistentClient(path=db_path)
        
    # 获取tool_vector集合
    collection = client.get_or_create_collection(name="tool_vector")
        
    # 检查ID是否存在
    exiting_documents = collection.get(ids=[tool_name])
    if not exiting_documents or not exiting_documents['ids']:
        raise HTTPException(status_code=404, detail=f"ID '{tool_name}' not found in the tool_vector collection.")
        
    # 从tool_vector集合中删除数据
    collection.delete(ids=[tool_name])
        
    # 同时从hypothetical_query集合中删除相关数据
    hypothetical_query_collection = client.get_or_create_collection(name="hypothetical_query")
    hypothetical_query_collection.delete(ids=[tool_name])
