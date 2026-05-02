FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=case_converter_service
ENV SERVICE_VERSION=0.1.0
ENV PORT=8011
ENV ENVIRONMENT=dev
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8011
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8011"]
