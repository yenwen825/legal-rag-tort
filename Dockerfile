FROM python:3.11-slim

# Python 雲端環境變數 (不寫入 pyc、Log 即時輸出)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 資安防禦：建立並切換為非特權使用者
RUN useradd -m appuser
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8080

CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 app:app