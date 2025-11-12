import chromadb
from fastapi import FastAPI
from contextlib import asynccontextmanager


# 接收db_path参数的版本
def create_lifespan(db_path_param):
    """
    创建接收db_path参数的生命周期管理函数
    
    Args:
        db_path_param: 数据库路径参数
    """
    @asynccontextmanager
    async def lifespan_with_args(app: FastAPI):
        """
        FastAPI应用的生命周期管理函数，使用传入的db_path参数
        在应用启动时初始化向量数据库，在应用关闭时执行清理操作
        
        Args:
            app: FastAPI应用实例（可以删除，因为在此函数中未使用）
        """
        # 使用传入的db_path参数
        chroma_db_path = db_path_param
        
        # 启动时执行
        print("应用启动，检查向量数据库...")
        
        # 检查是否存在db文件夹
        if not db_path_param.exists():
            print(f"创建数据库目录: {db_path_param}")
            db_path_param.mkdir(exist_ok=True)
        
        # 检查是否存在tools向量数据库
        try:
            # 尝试连接到Chroma数据库
            client = chromadb.PersistentClient(path=str(chroma_db_path))
            
            # 尝试获取或创建tool_vector集合
            tool_vector_collection = client.get_or_create_collection(name="tool_vector")
            print(f"Chroma向量数据库已就绪，位于: {chroma_db_path}")
            
            # 检查tool_vector集合中是否有数据
            tool_vector_count = tool_vector_collection.count()
            print(f"tool_vector集合中现有工具数量: {tool_vector_count}")
            
            # 尝试获取或创建hypothetical_query集合
            hypothetical_query_collection = client.get_or_create_collection(name="hypothetical_query")
            
            # 检查hypothetical_query集合中是否有数据
            hypothetical_query_count = hypothetical_query_collection.count()
            print(f"hypothetical_query集合中现有查询数量: {hypothetical_query_count}")
            
        except Exception as e:
            print(f"初始化Chroma向量数据库时出错: {e}")
            print("请确保已安装chromadb库: pip install chromadb")
        
        yield  # 应用运行期间
        
        # 关闭时执行
        print("应用关闭")
    
    return lifespan_with_args
