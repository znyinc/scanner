# Stock Scanner Deployment Guide

This guide covers deploying the Stock Scanner application in production environments.

## Prerequisites

- Docker and Docker Compose
- Git
- Make (optional, for using Makefile commands)

## Quick Start

### 1. Environment Setup

Copy the appropriate environment file and configure it:

```bash
# For production
cp .env.production .env

# For staging
cp .env.staging .env
```

**Important**: Update the following values in your `.env` file:
- `POSTGRES_PASSWORD`: Use a strong, unique password
- `SECRET_KEY`: Generate a secure random string
- `CORS_ORIGINS`: Set to your actual domain(s)
- `REACT_APP_API_URL`: Set to your API URL

### 2. Deploy

#### Using Make (Recommended)
```bash
# Deploy to production
make deploy ENV=production

# Deploy to staging
make deploy ENV=staging
```

#### Using Scripts Directly

**Linux/macOS:**
```bash
bash scripts/deploy.sh production
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 -Environment production
```

#### Manual Deployment
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml --env-file .env up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_USER` | Database username | stock_scanner | Yes |
| `POSTGRES_PASSWORD` | Database password | CHANGE_ME | Yes |
| `POSTGRES_DB` | Database name | stock_scanner | Yes |
| `SECRET_KEY` | Application secret key | CHANGE_ME | Yes |
| `CORS_ORIGINS` | Allowed CORS origins | https://yourdomain.com | Yes |
| `API_PORT` | Backend API port | 8000 | No |
| `FRONTEND_PORT` | Frontend port | 80 | No |
| `LOG_LEVEL` | Logging level | INFO | No |

### SSL Configuration

1. Place your SSL certificates in `nginx/ssl/`:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key

2. Update nginx configuration if needed in `nginx/nginx.conf`

## Services

The application consists of the following services:

- **Frontend**: React application served by Nginx
- **Backend**: FastAPI application
- **Database**: PostgreSQL database
- **Nginx**: Reverse proxy and load balancer (optional)

## Health Checks

The application provides several health check endpoints:

- `GET /health` - Comprehensive health check
- `GET /ready` - Readiness probe (Kubernetes)
- `GET /live` - Liveness probe (Kubernetes)
- `GET /metrics` - Application metrics

## Monitoring

### Endpoints

- **Health**: `http://localhost:8000/health`
- **Metrics**: `http://localhost:8000/metrics`
- **API Docs**: `http://localhost:8000/docs`

### Logs

View logs using Docker Compose:
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Backup and Restore

### Create Backup
```bash
# Using Make
make backup

# Using script directly
bash scripts/backup.sh
```

### Restore from Backup
```bash
# Using Make
make restore BACKUP_DATE=20240101_120000

# Using script directly
bash scripts/restore.sh 20240101_120000
```

## Maintenance

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and redeploy
make update ENV=production
```

### Scale Services
```bash
# Scale backend to 3 instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### View Service Status
```bash
# Using Make
make status

# Using Docker Compose
docker-compose -f docker-compose.prod.yml ps
```

## Troubleshooting

### Common Issues

1. **Services not starting**
   - Check environment variables are set correctly
   - Verify Docker has enough resources allocated
   - Check logs: `docker-compose -f docker-compose.prod.yml logs`

2. **Database connection issues**
   - Ensure PostgreSQL is running and healthy
   - Verify database credentials in environment file
   - Check network connectivity between services

3. **Frontend not loading**
   - Verify `REACT_APP_API_URL` is set correctly
   - Check if backend is accessible
   - Verify nginx configuration

### Debug Commands

```bash
# Check service health
curl http://localhost:8000/health

# View backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Access database
docker exec -it stockscanner-postgres-prod psql -U stock_scanner -d stock_scanner

# Check resource usage
docker stats
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files with production secrets
2. **SSL/TLS**: Always use HTTPS in production
3. **Database**: Use strong passwords and restrict network access
4. **Updates**: Keep Docker images and dependencies updated
5. **Backups**: Implement regular automated backups
6. **Monitoring**: Set up log aggregation and alerting

## CI/CD Pipeline

The application includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:

1. Runs tests on pull requests
2. Builds and pushes Docker images
3. Deploys to staging/production environments
4. Performs security scans

### Required Secrets

Configure these secrets in your GitHub repository:

- `REACT_APP_API_URL`: Frontend API URL
- Additional deployment secrets as needed

## Performance Tuning

### Database Optimization
- Configure PostgreSQL connection pooling
- Set appropriate shared_buffers and work_mem
- Monitor query performance

### Application Optimization
- Use multiple backend workers: `--workers 4`
- Configure appropriate timeout values
- Enable response caching where appropriate

### Infrastructure
- Use a CDN for static assets
- Implement database read replicas for scaling
- Consider container orchestration (Kubernetes) for large deployments

## Support

For issues and questions:
1. Check the logs first
2. Review this deployment guide
3. Check the application documentation
4. Create an issue in the repository