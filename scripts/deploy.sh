#!/bin/bash

# Stock Scanner Deployment Script
set -e

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.${ENVIRONMENT}"

echo "🚀 Deploying Stock Scanner to ${ENVIRONMENT} environment..."

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found!"
    echo "Please create the environment file with the required configuration."
    exit 1
fi

# Load environment variables
export $(cat $ENV_FILE | grep -v '^#' | xargs)

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data nginx/ssl

# Pull latest images (if using registry)
echo "📦 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull || true

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
timeout 300 bash -c '
    while true; do
        if docker-compose -f '$COMPOSE_FILE' ps | grep -q "unhealthy\|starting"; then
            echo "Waiting for services to be healthy..."
            sleep 10
        else
            break
        fi
    done
'

# Run health checks
echo "🏥 Running health checks..."
sleep 10

# Check backend health
if curl -f http://localhost:${API_PORT:-8000}/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -f $COMPOSE_FILE logs backend
    exit 1
fi

# Check frontend health
if curl -f http://localhost:${FRONTEND_PORT:-80}/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose -f $COMPOSE_FILE logs frontend
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "📊 Services status:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "🔗 Access URLs:"
echo "  Frontend: http://localhost:${FRONTEND_PORT:-80}"
echo "  Backend API: http://localhost:${API_PORT:-8000}"
echo "  API Docs: http://localhost:${API_PORT:-8000}/docs"
echo "  Health Check: http://localhost:${API_PORT:-8000}/health"
echo "  Metrics: http://localhost:${API_PORT:-8000}/metrics"