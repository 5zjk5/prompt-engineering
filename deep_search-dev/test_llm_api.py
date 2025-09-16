import asyncio
import os
from dotenv import load_dotenv
from api.llm_api import LLM
from logs.logger import define_log_level

# 加载环境变量
load_dotenv()

async def test_glm_model():
    """测试GLM模型调用"""
    # 初始化日志
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger, log_name = define_log_level(project_root, "test_llm_api")
    logger.info("开始测试GLM模型...")
    
    # 创建LLM实例
    llm = LLM(logger)
    
    # 测试简单对话
    prompt = "你好，请简单介绍一下你自己"
    try:
        response = await llm.infer(prompt, temperature=0.7)
        logger.info(f"GLM模型响应: {response}")
        logger.info("GLM模型测试成功!")
    except Exception as e:
        logger.error(f"GLM模型测试失败: {e}")


async def main():
    """主测试函数"""
    print("开始测试大模型API...")
    
    # 测试GLM模型
    await test_glm_model()
    
    print("\n所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main())