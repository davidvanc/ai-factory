FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=password_generator_service
ENV SERVICE_VERSION=0.1.0
ENV PORT=8013
ENV ENVIRONMENT=dev
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO
ENV AUTH_ENABLED=false
ENV AUTH_TOKENS=
ENV ALLOWED_ORIGINS=*
ENV RATE_LIMIT_ENABLED=false
ENV RATE_LIMIT_PER_MINUTE=60
ENV RATE_LIMIT_REDIS_URL=redis://localhost:6379/1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8013
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8013"]
