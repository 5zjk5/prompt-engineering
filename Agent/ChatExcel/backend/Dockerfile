# ── 后端镜像：Python + FastAPI ─────────────────────────────
# 用 3.11-slim 作为基础镜像，体积小且兼容 requirements 中的依赖
FROM python:3.11-slim

# 设置时区为东八区，避免日志时间和本地不一致
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 先单独拷贝依赖清单并安装，利用 Docker 分层缓存加速重建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝业务代码与运行所需的目录
COPY app ./app
COPY main.py ./main.py
COPY skills ./skills
COPY .env ./.env

# 运行时目录由 compose 挂载 volume 持久化，这里仅确保存在
RUN mkdir -p storage/db storage/uploads storage/duckdb storage/static/images logs

EXPOSE 7396

# 直接用 main.py 启动 uvicorn，与本地 start.bat 行为一致
CMD ["python", "main.py"]
