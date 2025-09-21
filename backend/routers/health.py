# routers/health.py - Health Check Router
from fastapi import APIRouter
from datetime import datetime
from services.ai_service import ai_service
from core.config import settings
import psutil
import sys

router = APIRouter()

@router.get("/health")
async def health_check():
    """Enhanced health check with system info"""
    ai_status = ai_service.get_status()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "ai_enabled": ai_status["ai_enabled"],
        "features": {
            "ai_processing": ai_status["ai_enabled"],
            "enhanced_parsing": True,
            "microservices_generation": True,
            "data_quality_analysis": True,
            "code_generation": True,
            "docker_support": True
        },
        "system_info": {
            "python_version": sys.version,
            "memory_usage_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": psutil.cpu_percent(),
        },
        "configuration": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "max_records_display": settings.MAX_RECORDS_DISPLAY,
            "caching_enabled": settings.ENABLE_CACHING
        }
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed system health information"""
    import platform
    
    ai_status = ai_service.get_status()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG,
            "ai_model": ai_status.get("model_name"),
            "cache_entries": ai_status.get("cache_size", 0)
        },
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_gb": round(memory.total / 1024**3, 2),
                "available_gb": round(memory.available / 1024**3, 2),
                "percent_used": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / 1024**3, 2),
                "free_gb": round(disk.free / 1024**3, 2),
                "percent_used": round((disk.used / disk.total) * 100, 2)
            }
        },
        "services": {
            "ai_service": "online" if ai_status["ai_enabled"] else "offline",
            "file_processing": "online",
            "data_analysis": "online",
            "code_generation": "online"
        }
    }