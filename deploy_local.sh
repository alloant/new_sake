#!/bin/bash

# Configuration
IMAGE_NAME="sake-api"
TAG="latest"
SYNOLOGY_USER="antonio"
SYNOLOGY_IP="100.119.49.72" # Update this to your Synology IP

echo "🚀 Building image locally..."
docker build -t $IMAGE_NAME:$TAG .

echo "📦 Piping image to Synology ($SYNOLOGY_IP)..."
rm ../sake-api.tar
docker save -o ../sake-api.tar $IMAGE_NAME:$TAG

echo "✅ Deployment finished!"
