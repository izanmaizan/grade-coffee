"""
Green Bean Grading API — entry point.

Jalankan dengan:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Dokumentasi API otomatis tersedia di:
    http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models.db_models import GradePrice, AnalysisHistory  # noqa: F401
from app.routers import analyze, history, prices
from app.seeders import seed_grades
from app.services.detector import BeanDetector


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifecycle: dijalankan saat startup & shutdown."""
    # 1) Buat tabel jika belum ada
    Base.metadata.create_all(bind=engine)

    # 2) Seed data grade default
    db = SessionLocal()
    try:
        added = seed_grades(db)
        if added:
            print(f"🌱 Seeded {added} grade default ke database.")
    finally:
        db.close()

    # 3) Pre-load YOLO model
    BeanDetector()

    print("\n" + "=" * 60)
    print("✅ Green Bean Grading API siap di http://localhost:8000")
    print("📖 Dokumentasi: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    yield


app = FastAPI(
    title="Green Bean Grading API",
    description=(
        "API untuk grading green coffee bean berbasis YOLOv8. "
        "Mendeteksi 18 jenis defect lalu menghitung grade SCA + harga."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — frontend React di port 5173 (Vite default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files — supaya gambar hasil bisa diakses dari frontend
app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_full_path)),
    name="uploads",
)

# Routers
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
    detector = BeanDetector()
    return {
        "status": "ok",
        "model_ready": detector.is_ready(),
        "device": detector.device,
    }