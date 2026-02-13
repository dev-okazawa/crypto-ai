FROM python:3.11-slim

WORKDIR /app

# 必要パッケージ
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソース
COPY . .

# ログディレクトリ
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
