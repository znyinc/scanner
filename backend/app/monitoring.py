"""
Monitoring and metrics collection for the Stock Scanner application.
"""
import time
import psutil
from typing import Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import get_logger


logger = get_logger(__name__)


class MetricsCollector:
    """Collect application metrics."""
    
    def __init__(self):
        self.request_count = 0
        self.request_duration_sum = 0.0
        self.error_count = 0
        self.start_time = datetime.utcnow()
    
    def record_request(self, duration: float, status_code: int):
        """Record a request metric."""
        self.request_count += 1
        self.request_duration_sum += duration
        
        if status_code >= 400:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = datetime.utcnow() - self.start_time
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "requests": {
                "total": self.request_count,
                "errors": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1),
                "avg_duration": self.request_duration_sum / max(self.request_count, 1),
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
            },
        }


# Global metrics collector
metrics_collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request metrics."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record metrics
            metrics_collector.record_request(duration, response.status_code)
            
            # Log slow requests
            if duration > 5.0:  # Log requests taking more than 5 seconds
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {duration:.2f}s"
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            metrics_collector.record_request(duration, 500)
            
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True
            )
            raise


def get_health_status() -> Dict[str, Any]:
    """Get application health status."""
    try:
        # Check system resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine health status
        status = "healthy"
        issues = []
        
        if memory.percent > 90:
            status = "unhealthy"
            issues.append("High memory usage")
        
        if disk.percent > 90:
            status = "unhealthy"
            issues.append("High disk usage")
        
        # Check if error rate is too high
        metrics = metrics_collector.get_metrics()
        if metrics["requests"]["error_rate"] > 0.1:  # More than 10% errors
            status = "degraded"
            issues.append("High error rate")
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "issues": issues,
            "checks": {
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "error_rate": metrics["requests"]["error_rate"],
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "issues": ["Health check failed"],
            "error": str(e)
        }