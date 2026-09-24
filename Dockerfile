# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Toolchains for the languages Testio grades out of the box.
# Build with --build-arg INSTALL_JAVA=true to add a JDK (~200 MB).
ARG INSTALL_JAVA=false
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libc6-dev nodejs ruby \
    && if [ "$INSTALL_JAVA" = "true" ]; then \
         apt-get install -y --no-install-recommends default-jdk-headless; \
       fi \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-deps .

RUN useradd --create-home --uid 10001 testio \
    && mkdir -p /data \
    && chown testio:testio /data

ENV TESTIO_APP_DB_PATH=/data/testio.db \
    TESTIO_CONFIG_DB_PATH=/data/test.db

USER testio
WORKDIR /home/testio
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/livez', timeout=4)"

CMD ["testio-server", "--host", "0.0.0.0", "--port", "8000"]
