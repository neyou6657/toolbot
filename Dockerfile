# HuggingFace Spaces Dockerfile for Telegram Bot
# 使用官方 Python 镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（curl_cffi 需要）
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY get_bininfo.py .
COPY bot.py .

# 设置环境变量（HuggingFace Spaces 会注入这些）
# TELEGRAM_BOT_TOKEN - 必须在 HuggingFace Spaces 设置中配置
# TELEGRAM_API_BASE - Cloudflare 反代地址
# TELEGRAM_API_BASE - 必须在 HuggingFace Spaces Secrets 中配置
ENV POLLING_INTERVAL="10"

# HuggingFace Spaces 需要暴露端口 7860（即使不用也需要）
# 创建一个简单的健康检查端点
EXPOSE 7860

# 运行机器人
CMD ["python", "bot.py"]
