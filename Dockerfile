FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

ENV TESTIO_APP_DB_PATH=/data/testio.db
ENV TESTIO_CONFIG_DB_PATH=/data/test.db

EXPOSE 8000

VOLUME ["/data"]

CMD ["python", "-m", "src.apps.server.main"]
