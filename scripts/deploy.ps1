# Stock Scanner Deployment Script for Windows
param(
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

# Configuration
$ComposeFile = "docker-compose.prod.yml"
$EnvFile = ".env.$Environment"

Write-Host "🚀 Deploying Stock Scanner to $Environment environment..." -ForegroundColor Green

# Check if environment file exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ Environment file $EnvFile not found!" -ForegroundColor Red
    Write-Host "Please create the environment file with the required configuration." -ForegroundColor Yellow
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "logs", "data", "nginx/ssl" | Out-Null

# Pull latest images (if using registry)
Write-Host "📦 Pulling latest images..." -ForegroundColor Blue
try {
    docker-compose -f $ComposeFile pull
} catch {
    Write-Host "Warning: Could not pull images, continuing with local builds..." -ForegroundColor Yellow
}

# Build and start services
Write-Host "🔨 Building and starting services..." -ForegroundColor Blue
docker-compose -f $ComposeFile --env-file $EnvFile up -d --build

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Blue
$timeout = 300
$elapsed = 0
do {
    Start-Sleep -Seconds 10
    $elapsed += 10
    $status = docker-compose -f $ComposeFile ps
    $unhealthy = $status | Select-String -Pattern "unhealthy|starting"
    
    if ($elapsed -gt $timeout) {
        Write-Host "❌ Timeout waiting for services to be healthy" -ForegroundColor Red
        docker-compose -f $ComposeFile logs
        exit 1
    }
} while ($unhealthy)

# Run health checks
Write-Host "🏥 Running health checks..." -ForegroundColor Blue
Start-Sleep -Seconds 10

# Load environment variables for port checking
$envVars = Get-Content $EnvFile | Where-Object { $_ -notmatch '^#' -and $_ -match '=' }
$apiPort = 8000
$frontendPort = 80

foreach ($line in $envVars) {
    $parts = $line -split '=', 2
    if ($parts[0] -eq 'API_PORT') { $apiPort = $parts[1] }
    if ($parts[0] -eq 'FRONTEND_PORT') { $frontendPort = $parts[1] }
}

# Check backend health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$apiPort/health" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is healthy" -ForegroundColor Green
    } else {
        throw "Backend returned status code $($response.StatusCode)"
    }
} catch {
    Write-Host "❌ Backend health check failed: $_" -ForegroundColor Red
    docker-compose -f $ComposeFile logs backend
    exit 1
}

# Check frontend health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$frontendPort/health" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend is healthy" -ForegroundColor Green
    } else {
        throw "Frontend returned status code $($response.StatusCode)"
    }
} catch {
    Write-Host "❌ Frontend health check failed: $_" -ForegroundColor Red
    docker-compose -f $ComposeFile logs frontend
    exit 1
}

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "📊 Services status:" -ForegroundColor Blue
docker-compose -f $ComposeFile ps

Write-Host ""
Write-Host "🔗 Access URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:$frontendPort" -ForegroundColor White
Write-Host "  Backend API: http://localhost:$apiPort" -ForegroundColor White
Write-Host "  API Docs: http://localhost:$apiPort/docs" -ForegroundColor White
Write-Host "  Health Check: http://localhost:$apiPort/health" -ForegroundColor White
Write-Host "  Metrics: http://localhost:$apiPort/metrics" -ForegroundColor White