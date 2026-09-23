import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.database import Base, engine
import app.models  # ensure models are loaded
from app.api.v1 import api_router
from app.websocket.router import router as websocket_router

# Auto-create tables if running in development mode
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ShopFlow — Real-Time E-Commerce Order & Inventory Platform",
    description="""
    Production-style E-Commerce API featuring:
    * High-concurrency inventory reservation with PostgreSQL row-level locking (SELECT ... FOR UPDATE)
    * Centralized order status state machine & simulated payment gateway
    * Transactional Outbox pattern & asynchronous RabbitMQ/Celery workers
    * Real-time WebSocket order tracking (/ws/orders/{id})
    * Redis cache-aside & sliding-window rate limiting
    * JWT authentication with refresh token rotation and RBAC
    * AI-powered hybrid recommendation engine
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured Logging & Request ID Middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()

    # Process request
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        
        # Avoid cluttering logs on health probes
        if not request.url.path.startswith("/health"):
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
            extra={"request_id": request_id, "duration_ms": duration_ms}
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred."
                },
                "request_id": request_id
            }
        )

# Standardized Error Responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "HTTP_ERROR")
        message = detail.get("message", "An error occurred")
        details = detail.get("details", {})
    else:
        code = "HTTP_ERROR"
        message = str(detail)
        details = {}

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            },
            "request_id": request_id
        }
    )

from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload.",
                "details": {"validation_errors": jsonable_encoder(exc.errors())}
            },
            "request_id": request_id
        }
    )

# Include API and WebSocket routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router)
