FROM python:3.11-slim

WORKDIR /app

COPY ml-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ml-service /app/ml-service
COPY ml-models /app/ml-models

EXPOSE 8001

CMD ["uvicorn", "ml-service.app:app", "--host", "0.0.0.0", "--port", "8001"]


