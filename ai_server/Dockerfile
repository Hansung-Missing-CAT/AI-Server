FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 기본: FastAPI 서버. 워커는 docker-compose에서 CMD override로 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
