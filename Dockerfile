# --- STAGE 1: Builder (Remains the same) ---
FROM python:3.14.4-slim AS builder
#RUN apk add --no-cache build-base git
WORKDIR /setup
COPY requirements.txt .

# Install build tools required to compile C extensions (gcc, make, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt

# --- STAGE 2: Final ---
FROM python:3.14.4-slim
WORKDIR /app

# Copy EVERYTHING (including gunicorn and uvicorn) from the builder
COPY --from=builder /install /usr/local

# Copy your application files
COPY . /app

# Production Command
CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--keyfile", "/cert/server.key", \
     "--certfile", "/cert/server.crt", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

#CMD ["gunicorn", "main:app", \
#     "--workers", "4", \
#     "--worker-class", "uvicorn.workers.UvicornWorker", \
#     "--bind", "0.0.0.0:8000", \
#     "--forwarded-allow-ips", "*", \
#     "--keyfile", "/cert/server.key", \
#     "--certfile", "/cert/server.crt", \
#     "--access-logfile", "-", \
#     "--error-logfile", "-", \
#     "--root-path", "/sake"]
