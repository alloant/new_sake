# syntax=docker/dockerfile:1.4
FROM sake-base:latest

WORKDIR /app

COPY . /app


CMD ["uvicorn main:app --reload --host 0.0.0.0 --ssl-keyfile /cert/server.key --ssl-certfile /cert/server.crt"]
