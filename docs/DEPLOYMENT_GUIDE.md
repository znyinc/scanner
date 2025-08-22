# Stock Scanner Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Setup](#database-setup)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 10 GB available space
- **Network**: Stable internet connection for market data
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+

### Recommended Requirements
- **CPU**: 4+ cores, 3.0 GHz
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **Network**: High-speed internet (100+ Mbps)
- **OS**: Linux (Ubuntu 22.04 LTS)

### Software Dependencies
- **Python**: 3.9 or higher
- **Node.js**: 16.0 or higher
- **PostgreSQL**: 13.0 or higher
- **Git**: Latest version

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd stock-scanner
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
python -m venv venv

# On Linux/macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate

pip install -r requirements.txt
```

#### Environment Configuration
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/stock_scanner
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=stock_scanner
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# External APIs
YFINANCE_TIMEOUT=30
YFINANCE_RETRY_COUNT=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Database Setup
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE stock_scanner;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE stock_scanner TO your_username;
\q

# Initialize database schema
python app/init_db.py
```

#### Start Backend Server
```bash
python run_server.py
```

The backend API will be available at `http://localhost:8000`

### 3. Frontend Setup

#### Install Node.js Dependencies
```bash
cd frontend
npm install
```

#### Environment Configuration
```bash
cp .env.example .env.local
```

Edit `.env.local` file:
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development
```

#### Start Frontend Development Server
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

### 4. Verify Installation

1. Open browser to `http://localhost:3000`
2. Navigate to Scanner tab
3. Enter a stock symbol (e.g., "AAPL")
4. Click "Start Scan"
5. Verify results appear

## Production Deployment

### 1. Server Preparation

#### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### Install Required Software
```bash
# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip

# Install Node.js 16+
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Nginx
sudo apt install nginx

# Install Supervisor (for process management)
sudo apt install supervisor

# Install Git
sudo apt install git
```

### 2. Application Deployment

#### Clone and Setup Application
```bash
# Create application directory
sudo mkdir -p /opt/stock-scanner
sudo chown $USER:$USER /opt/stock-scanner

# Clone repository
cd /opt/stock-scanner
git clone <repository-url> .

# Setup backend
cd backend
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
npm run build
```

#### Production Environment Configuration
```bash
# Backend environment
cd /opt/stock-scanner/backend
cp .env.example .env
```

Edit production `.env`:
```env
DATABASE_URL=postgresql://stock_scanner:secure_password@localhost:5432/stock_scanner_prod
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=your-very-secure-secret-key
CORS_ORIGINS=https://yourdomain.com
```

### 3. Database Configuration

#### Setup Production Database
```bash
sudo -u postgres psql
CREATE DATABASE stock_scanner_prod;
CREATE USER stock_scanner WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE stock_scanner_prod TO stock_scanner;
\q

# Initialize schema
cd /opt/stock-scanner/backend
source venv/bin/activate
python app/init_db.py
```

#### Configure PostgreSQL for Production
```bash
sudo nano /etc/postgresql/13/main/postgresql.conf
```

Key settings:
```conf
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Connection settings
max_connections = 100

# Logging
log_statement = 'all'
log_duration = on
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 4. Web Server Configuration

#### Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/stock-scanner
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend static files
    location / {
        root /opt/stock-scanner/frontend/build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/stock-scanner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Process Management

#### Supervisor Configuration
```bash
sudo nano /etc/supervisor/conf.d/stock-scanner.conf
```

```ini
[program:stock-scanner-api]
command=/opt/stock-scanner/backend/venv/bin/python run_server.py
directory=/opt/stock-scanner/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/stock-scanner/api.log
environment=PATH="/opt/stock-scanner/backend/venv/bin"

[program:stock-scanner-worker]
command=/opt/stock-scanner/backend/venv/bin/python -m celery worker -A app.celery_app
directory=/opt/stock-scanner/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/stock-scanner/worker.log
environment=PATH="/opt/stock-scanner/backend/venv/bin"
```

Create log directory:
```bash
sudo mkdir -p /var/log/stock-scanner
sudo chown www-data:www-data /var/log/stock-scanner
```

Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 6. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Docker Deployment

### 1. Docker Compose Setup

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: stock_scanner
      POSTGRES_USER: stock_scanner
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U stock_scanner"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://stock_scanner:secure_password@postgres:5432/stock_scanner
      API_HOST: 0.0.0.0
      API_PORT: 8000
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend/logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      REACT_APP_API_URL: http://localhost:8000/api

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Backend Dockerfile

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "run_server.py"]
```

### 3. Frontend Dockerfile

Create `frontend/Dockerfile`:
```dockerfile
# Build stage
FROM node:16-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 4. Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=3

# Update application
git pull
docker-compose build
docker-compose up -d
```

## Environment Configuration

### Development Environment
```env
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:pass@localhost:5432/stock_scanner_dev
CORS_ORIGINS=http://localhost:3000
```

### Staging Environment
```env
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db:5432/stock_scanner_staging
CORS_ORIGINS=https://staging.yourdomain.com
```

### Production Environment
```env
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@prod-db:5432/stock_scanner_prod
CORS_ORIGINS=https://yourdomain.com
SECRET_KEY=very-secure-production-key
```

## Database Setup

### Initial Schema Creation
```sql
-- Run this script to create initial database schema
-- File: backend/database/init.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create scan_results table
CREATE TABLE scan_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    symbols_scanned JSONB NOT NULL,
    signals_found JSONB NOT NULL,
    settings_used JSONB NOT NULL,
    execution_time DECIMAL(10,3) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create backtest_results table
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    symbols JSONB NOT NULL,
    trades JSONB NOT NULL,
    performance JSONB NOT NULL,
    settings_used JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trades table
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    entry_date TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL(12,4) NOT NULL,
    exit_date TIMESTAMPTZ,
    exit_price DECIMAL(12,4),
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('long', 'short')),
    pnl DECIMAL(12,4),
    pnl_percent DECIMAL(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_scan_results_timestamp ON scan_results(timestamp DESC);
CREATE INDEX idx_backtest_results_timestamp ON backtest_results(timestamp DESC);
CREATE INDEX idx_backtest_results_date_range ON backtest_results(start_date, end_date);
CREATE INDEX idx_trades_backtest_id ON trades(backtest_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_entry_date ON trades(entry_date);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_scan_results_updated_at BEFORE UPDATE ON scan_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_backtest_results_updated_at BEFORE UPDATE ON backtest_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Database Migrations
```bash
# Create migration script
cd backend
python -c "
from app.database import get_database
from app.init_db import create_tables
create_tables()
print('Database initialized successfully')
"
```

## Monitoring and Logging

### 1. Application Logging

Configure logging in `backend/app/config.py`:
```python
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Create logs directory
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5),
            logging.StreamHandler()
        ]
    )
```

### 2. System Monitoring

#### Install Monitoring Tools
```bash
# Install htop for system monitoring
sudo apt install htop

# Install PostgreSQL monitoring
sudo apt install postgresql-contrib
```

#### Health Check Endpoint
Add to `backend/app/main.py`:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }
```

### 3. Log Rotation

Configure logrotate:
```bash
sudo nano /etc/logrotate.d/stock-scanner
```

```
/var/log/stock-scanner/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        supervisorctl restart stock-scanner-api
    endscript
}
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
psql -h localhost -U stock_scanner -d stock_scanner_prod

# Check logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

#### 2. API Server Issues
```bash
# Check supervisor status
sudo supervisorctl status

# Restart API server
sudo supervisorctl restart stock-scanner-api

# Check API logs
sudo tail -f /var/log/stock-scanner/api.log
```

#### 3. Frontend Issues
```bash
# Check Nginx status
sudo systemctl status nginx

# Test Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

#### 4. Performance Issues
```bash
# Monitor system resources
htop

# Check database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/health"
```

### Debugging Steps

1. **Check System Resources**
   ```bash
   df -h  # Disk space
   free -h  # Memory usage
   top  # CPU usage
   ```

2. **Verify Services**
   ```bash
   sudo systemctl status postgresql nginx supervisor
   ```

3. **Check Application Logs**
   ```bash
   sudo tail -f /var/log/stock-scanner/*.log
   ```

4. **Test Database Connection**
   ```bash
   python -c "
   from app.database import get_database
   db = get_database()
   print('Database connection successful')
   "
   ```

5. **Verify API Endpoints**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/settings
   ```

### Performance Optimization

#### Database Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM scan_results ORDER BY timestamp DESC LIMIT 10;

-- Update table statistics
ANALYZE scan_results;
ANALYZE backtest_results;

-- Vacuum tables
VACUUM ANALYZE;
```

#### Application Optimization
```python
# Enable connection pooling
DATABASE_URL=postgresql://user:pass@host:port/db?pool_size=20&max_overflow=30

# Configure async settings
ASYNC_POOL_SIZE=10
ASYNC_MAX_OVERFLOW=20
```

---

*This deployment guide is regularly updated. Check for the latest version to ensure you have current deployment procedures.*