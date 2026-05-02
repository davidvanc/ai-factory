FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_PORT=8006

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8006
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8006"]
