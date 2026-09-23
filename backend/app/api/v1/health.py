from fastapi import APIRouter, Response, status
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.redis import redis_client
from app.core.config import settings

router = APIRouter(tags=["Health & Observability"])

@router.get("/health")
def health_check():
    """Basic health check indicating process is responding."""
    return {"status": "ok", "service": "shopflow-api", "environment": settings.ENVIRONMENT}

@router.get("/health/live")
def liveness_probe():
    """Liveness probe for container orchestrator (Kubernetes / ECS)."""
    return {"status": "alive"}

@router.get("/health/ready")
def readiness_probe():
    """
    Readiness probe validating database connectivity and cache responsiveness.
    """
    checks = {
        "database": False,
        "redis": False,
    }

    # Test DB
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)
    finally:
        db.close()

    # Test Redis
    checks["redis"] = redis_client.ping()

    all_ready = checks["database"]  # DB is critical requirement
    status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(
        content=f'{{"status": "{"ready" if all_ready else "not_ready"}", "checks": {str(checks).replace("True", "true").replace("False", "false")}}}',
        media_type="application/json",
        status_code=status_code
    )

@router.get("/metrics")
def prometheus_metrics():
    """Expose Prometheus metrics for Prometheus scraping."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
