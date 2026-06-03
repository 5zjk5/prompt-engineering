import time
from types import SimpleNamespace


def call_llm_with_retry(llm, prompt, logger, max_retries=3):
    """
    调用 LLM 并带有重试机制

    参数:
        llm: LLM 模型对象
        prompt: 提示词
        max_retries: 最大重试次数，默认3次

    返回:
        LLM 响应对象，包含 content 属性。如果3次都失败返回包含错误信息的对象
    """
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)
            return response
        except Exception as e:
            error_msg = str(e)

            # 检查是否是速率限制错误
            if "1302" in error_msg and "速率限制" in error_msg:  # 智谱
                if attempt < max_retries - 1:
                    logger.warning(
                        f"速率限制错误，等待60秒后重试 (尝试 {attempt + 1}/{max_retries})"
                    )
                    time.sleep(60)
                    continue

            # 其他错误
            if attempt < max_retries - 1:
                logger.error(
                    f"调用失败，准备重试 (尝试 {attempt + 1}/{max_retries}), 错误信息: {error_msg}"
                )
                time.sleep(10)
                continue

            logger.error(f"3次重试全部失败")
            error_response = SimpleNamespace()
            error_response.content = "大模型error"
            return error_response

    error_response = SimpleNamespace()
    error_response.content = "大模型error"
    return error_response
