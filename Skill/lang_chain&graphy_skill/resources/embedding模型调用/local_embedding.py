# pip install huggingface_hub
# pip install -U langchain-huggingface sentence_transformers
# https://docs.langchain.com/oss/python/integrations/text_embedding/huggingfacehub

from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from pathlib import Path


def load_embedding_model(model_path, device="cpu"):
    """
    加载嵌入模型
    
    Args:
        model_path (str): 模型路径或HuggingFace仓库ID
        device (str): 设备类型，"cpu" 或 "cuda"，默认为"cpu"
    
    Returns:
        HuggingFaceEmbeddings: 嵌入模型实例
    """
    # 检查是本地路径还是HuggingFace仓库ID
    if Path(model_path).exists():
        print(f"加载本地模型: {model_path}")
        embeddings = HuggingFaceEmbeddings(
            model_name=model_path, 
            model_kwargs={'device': device}
        )
    else:
        print(f"加载HuggingFace仓库模型: {model_path}")
        embeddings = HuggingFaceEmbeddings(
            model_name=model_path, 
            model_kwargs={'device': device}
        )
    
    return embeddings


if __name__ == "__main__":
    # 直接测试示例
    try:
        # 加载模型
        model_path = r'D:\project\model\bge_small_zh_v1.5'
        embeddings = load_embedding_model(model_path, device="cpu")
        
        # 测试模型
        result = embeddings.embed_query("你好")
        print("嵌入结果:", result[:5], "...")  # 只打印前5个值
        print("嵌入向量长度:", len(result))
        
    except Exception as e:
        print(f"加载或测试模型时出错: {e}")
