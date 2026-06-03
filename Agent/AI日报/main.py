import time
import traceback
from fastapi import FastAPI
from datetime import datetime
from utils.logger import define_log_level
from workflow.today_news import TodayNews
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()


@app.get("/hello")
async def hello():
    """测试连接接口"""
    return {"message": "hello"}


@app.get("/api/today_news")
async def search():
    """获取今日新闻"""
    now = datetime.now()
    log_name = f"{now.strftime('%Y%m%d_%H_%M')}_today_news.log"
    logger = define_log_level(log_name)
    try:
        start_time = time.time()
        
        today_news = TodayNews(logger)
        news = await today_news.get_today_news()
        
        end_time = time.time()
        logger.info(f"获取今日新闻耗时: {end_time - start_time} 秒")
        return {
            "today_news": news,
            "time": end_time - start_time
        }
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7396, ssl_keyfile="/root/cert.key", ssl_certfile="/root/cert.pem")
