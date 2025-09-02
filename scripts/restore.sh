#!/bin/bash

# Stock Scanner Restore Script
set -e

# Configuration
BACKUP_DIR="/backups/stock-scanner"
COMPOSE_FILE="docker-compose.prod.yml"

# Database configuration
DB_CONTAINER="stockscanner-postgres-prod"
DB_NAME=${POSTGRES_DB:-stock_scanner}
DB_USER=${POSTGRES_USER:-stock_scanner}

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la "$BACKUP_DIR" | grep "database_" | awk '{print $9}' | sed 's/database_//' | sed 's/.sql//'
    exit 1
fi

BACKUP_DATE=$1

echo "🔄 Starting restore process for backup: $BACKUP_DATE"

# Check if backup files exist
DB_BACKUP="$BACKUP_DIR/database_$BACKUP_DATE.sql"
DATA_BACKUP="$BACKUP_DIR/data_$BACKUP_DATE.tar.gz"
LOGS_BACKUP="$BACKUP_DIR/logs_$BACKUP_DATE.tar.gz"
CONFIG_BACKUP="$BACKUP_DIR/config_$BACKUP_DATE.tar.gz"

if [ ! -f "$DB_BACKUP" ]; then
    echo "❌ Database backup file not found: $DB_BACKUP"
    exit 1
fi

# Confirm restore operation
read -p "⚠️ This will overwrite existing data. Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# Stop services
echo "🛑 Stopping services..."
docker-compose -f $COMPOSE_FILE down

# Restore database
echo "📊 Restoring database..."
docker-compose -f $COMPOSE_FILE up -d postgres
sleep 10

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
timeout 60 bash -c '
    while ! docker exec '$DB_CONTAINER' pg_isready -U '$DB_USER' -d '$DB_NAME'; do
        sleep 2
    done
'

# Drop and recreate database
docker exec $DB_CONTAINER psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec $DB_CONTAINER psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# Restore database from backup
docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < "$DB_BACKUP"

# Restore application data
if [ -f "$DATA_BACKUP" ]; then
    echo "📁 Restoring application data..."
    rm -rf data/
    tar -xzf "$DATA_BACKUP"
fi

# Restore logs (optional)
if [ -f "$LOGS_BACKUP" ]; then
    echo "📝 Restoring logs..."
    rm -rf logs/
    tar -xzf "$LOGS_BACKUP"
fi

# Restore configuration (optional)
if [ -f "$CONFIG_BACKUP" ]; then
    echo "⚙️ Configuration backup found, but not automatically restored to prevent overwriting current config"
    echo "To restore configuration manually, extract: $CONFIG_BACKUP"
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Verify restore
echo "🏥 Verifying restore..."
if curl -f http://localhost:${API_PORT:-8000}/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -f $COMPOSE_FILE logs backend
    exit 1
fi

echo "🎉 Restore completed successfully!"
echo "📊 Services status:"
docker-compose -f $COMPOSE_FILE ps