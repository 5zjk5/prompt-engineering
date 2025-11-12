import uvicorn
import traceback
import time
import asyncio
from art import text2art
from fastapi import FastAPI, HTTPException, Request
from pathlib import Path
from logs.logger import define_log_level
from pydantic import BaseModel
from deepsearch.main_deepsearch import DeepSearch
from deepsearch.utils.parse_data import verify_params


app = FastAPI()
VERSION = '0.1'
project_root = Path(__file__).resolve().parent


class DeepSearchRequest(BaseModel):
    topic: str = ""
    

@app.post("/api/deep_search")
async def deep_search(request: DeepSearchRequest, fastapi_request: Request):
    """
    处理 deepsearch 请求的主接口

    Args:
        request: FastAPI请求对象

    Returns:
        JSON响应
    """
    # 参数
    topic = request.topic

    # 创建日志
    logger, log_name = define_log_level(project_root, topic)
    logger.info(f"日志已创建：{log_name}")

    try:
        start = time.time()

        # 参数校验
        topic = verify_params(topic)
        logger.info(f"参数校验成功！主题：{topic}")

        # 创建带取消功能的任务
        deepsearch_task = asyncio.create_task(
            DeepSearch(topic, project_root, logger).run()
        )

        # 添加请求取消监听
        stop_event = asyncio.Event()
        request_task = asyncio.create_task(request_disconnect_handler(fastapi_request, stop_event))

        # 等待任务完成或取消
        done, pending = await asyncio.wait(
            [deepsearch_task, request_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # 处理取消信号
        if not deepsearch_task.done():
            logger.warning("用户取消了请求，正在终止任务...")
            deepsearch_task.cancel()
            try:
                await deepsearch_task
            except asyncio.CancelledError:
                logger.info("任务已成功终止")
            return {
                "status": 499,  # Nginx定义的客户端关闭连接状态码
                "msg": "请求已被用户取消"
            }

        # 获取正常结果
        result = deepsearch_task.result()

        end = time.time()
        logger.info(f"深度搜索总共耗时：{end - start}s")

        return {
            "status": 200,
            "time": end - start,
            "msg": "success",
            "data": result
        }
    except HTTPException as e:
        logger.error(e.detail)
        return {
            "status": 400,
            "msg": 'fail',
            "data": e.detail
        }
    except Exception as e:
        logger.error(traceback.format_exc())
        return {
            "status": 500,
            "msg": "fail",
            "data": str(e)
        }


async def request_disconnect_handler(request: Request, stop_event: asyncio.Event):
    """监听客户端连接状态"""
    while not stop_event.is_set():
        if await request.is_disconnected():
            stop_event.set()
            return
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    print(text2art('DEEPSEARCH'))
    print('Version:', VERSION)

    uvicorn.run(app, host="0.0.0.0", port=7396, reload=False)
