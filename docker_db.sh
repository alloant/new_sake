#!/usr/bin/sh
docker network create my-app-network

docker run -d \
  -p 3306:3306 \
  --network my-app-network \
  --name my-mariadb \
  -e MARIADB_ROOT_PASSWORD='1234qwer' \
  -e MARIADB_ROOT_HOST=% \
  -v mariadb_data:/var/lib/mysql \
  mariadb:latest

docker run -d \
  --name my-redis \
  --network my-app-network \
  -v redis_data:/data \
  -p 6379:6379 \
  redis:latest redis-server --appendonly yes
