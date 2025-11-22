FROM python:3.9-slim as base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "web_app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==================== 生产环境镜像 ====================
FROM base as production

# 设置生产环境变量
ENV APP_ENV=production
ENV LOG_LEVEL=INFO
ENV DEBUG=false

# 安装额外的生产依赖
RUN pip install gunicorn==21.2.0

# 使用gunicorn启动
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "python:config.gunicorn_config", "web_app.main:app"]

# ==================== 开发环境镜像 ====================
FROM base as development

# 设置开发环境变量
ENV APP_ENV=development
ENV LOG_LEVEL=DEBUG
ENV DEBUG=true

# 安装开发工具
RUN pip install pytest pytest-asyncio black flake8 mypy

# 开发模式启动
CMD ["uvicorn", "web_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

