#!/bin/bash

# Stock Scanner Backup Script
set -e

# Configuration
BACKUP_DIR="/backups/stock-scanner"
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="docker-compose.prod.yml"

# Database configuration
DB_CONTAINER="stockscanner-postgres-prod"
DB_NAME=${POSTGRES_DB:-stock_scanner}
DB_USER=${POSTGRES_USER:-stock_scanner}

echo "🗄️ Starting backup process..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
echo "📊 Backing up database..."
docker exec $DB_CONTAINER pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/database_$DATE.sql"

# Backup application data
echo "📁 Backing up application data..."
if [ -d "data" ]; then
    tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" data/
fi

# Backup logs
echo "📝 Backing up logs..."
if [ -d "logs" ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/
fi

# Backup configuration
echo "⚙️ Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    .env.production \
    .env.staging \
    docker-compose.prod.yml \
    nginx/ \
    scripts/ \
    || true

# Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete || true
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete || true

# Create backup summary
echo "📋 Creating backup summary..."
cat > "$BACKUP_DIR/backup_$DATE.txt" << EOF
Stock Scanner Backup Summary
Date: $(date)
Database: $DB_NAME
Files backed up:
- Database dump: database_$DATE.sql
- Application data: data_$DATE.tar.gz
- Logs: logs_$DATE.tar.gz
- Configuration: config_$DATE.tar.gz

Backup location: $BACKUP_DIR
EOF

echo "✅ Backup completed successfully!"
echo "📍 Backup location: $BACKUP_DIR"
ls -la "$BACKUP_DIR" | tail -10