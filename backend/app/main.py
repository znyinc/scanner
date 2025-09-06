import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .api import scan, backtest, history, market_data
from .api import settings as settings_router
from .config import get_settings
from .logging_config import setup_logging, get_logger
from .monitoring import MetricsMiddleware, metrics_collector, get_health_status


# Set up logging
setup_logging()
logger = get_logger(__name__)

# Global shutdown flag
shutdown_event = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_event
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event = True


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Stock Scanner API...")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Stock Scanner API...")
    # Add any cleanup logic here (close database connections, etc.)


app = FastAPI(
    title="Stock Scanner API",
    version="1.0.0",
    description="EMA-ATR based stock scanner with backtesting capabilities",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Add monitoring middleware
app.add_middleware(MetricsMiddleware)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(scan.router)
app.include_router(backtest.router)
app.include_router(history.router)
app.include_router(settings_router.router)
app.include_router(market_data.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Stock Scanner API",
        "version": "1.0.0",
        "environment": settings.environment,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Comprehensive health check endpoint."""
    return get_health_status()


@app.get("/metrics")
async def get_metrics():
    """Get application metrics."""
    return metrics_collector.get_metrics()


@app.get("/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    # Add any readiness checks here (database connectivity, etc.)
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@app.get("/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    global shutdown_event
    if shutdown_event:
        return {"status": "shutting_down", "timestamp": datetime.utcnow().isoformat()}
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}