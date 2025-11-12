import chromadb
import json
from typing import Optional, List, Dict, Any


async def select_tool_from_db(db_path: str, tool_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    根据工具名称从数据库中查询工具信息和假设性问题
    
    Args:
        db_path: 数据库路径
        tool_name: 工具名称（ID），如果为None则返回所有工具

    Returns:
        工具信息列表，包含工具数据和假设性问题
    """
    # 连接到Chroma数据库
    client = chromadb.PersistentClient(path=db_path)
    
    # 获取tool_vector集合
    tool_vector_collection = client.get_or_create_collection(name="tool_vector")
    
    # 获取hypothetical_query集合
    hypothetical_query_collection = client.get_or_create_collection(name="hypothetical_query")
    
    # 如果提供了tool_name，则查询特定工具
    if tool_name:
        # 检查ID是否存在
        existing_documents = tool_vector_collection.get(ids=[tool_name])
        if not existing_documents or not existing_documents['ids']:
            return []
        
        # 解析工具数据
        tools = []
        for i, doc_id in enumerate(existing_documents['ids']):
            tool_info = {}
            
            # 解析工具数据
            try:
                tool_data = json.loads(existing_documents['documents'][i])
                tool_info["tool_data"] = tool_data
            except json.JSONDecodeError:
                # 如果无法解析JSON，返回原始字符串
                tool_info["tool_data"] = {"id": doc_id, "content": existing_documents['documents'][i]}
            
            # 查询对应的假设性问题
            try:
                hypothetical_documents = hypothetical_query_collection.get(ids=[doc_id])
                if hypothetical_documents and hypothetical_documents['ids']:
                    tool_info["hypothetical_query"] = hypothetical_documents['documents'][0]
                else:
                    tool_info["hypothetical_query"] = None
            except Exception:
                tool_info["hypothetical_query"] = None
            
            tools.append(tool_info)
        
        return tools
    else:
        # 如果没有提供tool_name，返回所有工具
        all_documents = tool_vector_collection.get()
        tools = []
        
        if all_documents and all_documents['ids']:
            for i, doc_id in enumerate(all_documents['ids']):
                tool_info = {}
                
                # 解析工具数据
                try:
                    tool_data = json.loads(all_documents['documents'][i])
                    # 添加ID到工具数据中
                    if 'name' not in tool_data:
                        tool_data['name'] = doc_id
                    tool_info["tool_data"] = tool_data
                except (json.JSONDecodeError, IndexError):
                    # 如果无法解析JSON，返回原始字符串
                    tool_info["tool_data"] = {"id": doc_id, "content": all_documents['documents'][i] if i < len(all_documents['documents']) else ""}
                
                # 查询对应的假设性问题
                try:
                    hypothetical_documents = hypothetical_query_collection.get(ids=[doc_id])
                    if hypothetical_documents and hypothetical_documents['ids']:
                        tool_info["hypothetical_query"] = hypothetical_documents['documents'][0]
                    else:
                        tool_info["hypothetical_query"] = None
                except Exception:
                    tool_info["hypothetical_query"] = None
                
                tools.append(tool_info)
        
        return tools
        