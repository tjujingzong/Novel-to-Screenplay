FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（用于 pdfplumber 等）
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存层
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /data/uploads /data/outputs

ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

# Render 自动注入 PORT 环境变量，默认 8000
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
