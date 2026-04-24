# --- STAGE 1: Builder (Remains the same) ---
FROM python:3.14.3-alpine3.23 AS builder
RUN apk add --no-cache build-base git
WORKDIR /setup
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt

# --- STAGE 2: Final ---
FROM python:3.14.3-alpine3.23
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
