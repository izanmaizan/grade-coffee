"""
Green Bean Grading API — entry point.

Jalankan dengan:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Dokumentasi API otomatis tersedia di:
    http://localhost:8000/docs
"""
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.config import settings
from app.database import SessionLocal, check_db_health, wait_for_db
from app.logging_config import get_logger, request_id_ctx, setup_logging
from app.models.db_models import GradePrice, AnalysisHistory  # noqa: F401
from app.rate_limit import limiter
from app.routers import analyze, history, prices
from app.seeders import seed_grades
from app.services import storage
from app.services.detector import BeanDetector


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifecycle: dijalankan saat startup & shutdown."""
    # 1) Tunggu DB siap dengan retry (#49)
    wait_for_db()

    # 2) Seed data grade default (skema dikelola Alembic, lihat alembic/) (#9)
    db = SessionLocal()
    try:
        added = seed_grades(db)
        if added:
            logger.info("Seed grade default", extra={"added": added})
    finally:
        db.close()

    # 3) Bersihkan upload lama sesuai retensi + cek disk (#18)
    storage.cleanup_old_uploads()
    storage.check_disk_space()

    # 4) Pre-load YOLO model (gagal keras bila wajib & tidak ada) (#13)
    BeanDetector()

    logger.info(
        "Green Bean Grading API siap",
        extra={"env": settings.APP_ENV, "docs": "/docs"},
    )
    yield

    # ---- Shutdown: graceful (#23) ----
    logger.info("Shutdown: menutup koneksi database")
    from app.database import engine

    engine.dispose()


app = FastAPI(
    title="Green Bean Grading API",
    description=(
        "API untuk grading green coffee bean berbasis YOLOv8. "
        "Mendeteksi 18 jenis defect lalu menghitung grade SCA + harga."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---- Rate limiting (#3) ----
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---- HTTPS redirect (opsional, untuk production di belakang TLS) (#47) ----
if settings.FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

# ---- CORS — method & header eksplisit, tidak wildcard (#2) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
    expose_headers=["X-Request-ID"],
)


# ---- Middleware: correlation/request ID + security headers (#24, #43) ----
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    token = request_id_ctx.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)

    response.headers["X-Request-ID"] = request_id
    # Security headers (#43)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data: blob:; "
        "style-src 'self' 'unsafe-inline'"
    )
    if settings.FORCE_HTTPS:
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
    return response


# ---- Middleware: batas ukuran body request global (#40) ----
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_body_bytes:
        return JSONResponse(
            status_code=413,
            content={"detail": (
                f"Ukuran request melebihi batas {settings.MAX_REQUEST_BODY_MB} MB"
            )},
        )
    return await call_next(request)


# ---- Metrics Prometheus di /metrics (#41) ----
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["monitoring"])

# ---- Static files — gambar hasil ----
app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_full_path)),
    name="uploads",
)

# ---- Routers (versioned /api/v1) (#38) ----
app.include_router(analyze.router)
app.include_router(prices.router)
app.include_router(history.router)


@app.get("/", tags=["health"])
def root():
    return {
        "name": "Green Bean Grading API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health():
    """Health check menyeluruh: DB + model + disk (#8)."""
    detector = BeanDetector()
    db_ok = check_db_health()
    disk = storage.get_disk_usage()

    healthy = db_ok  # DB wajib; model boleh menyusul
    body = {
        "status": "ok" if healthy else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "model_ready": detector.is_ready(),
        "device": detector.device,
        "disk_percent_used": disk.percent_used,
    }
    return JSONResponse(status_code=200 if healthy else 503, content=body)
