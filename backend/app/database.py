"""
Setup database SQLAlchemy untuk MySQL.

Catatan arsitektur (#34): driver yang dipakai adalah PyMySQL yang bersifat
sinkron. Migrasi penuh ke async (asyncmy/aiomysql + AsyncSession) berisiko tinggi
dan akan menyentuh seluruh router. Untuk beban kerja ini — query DB ringan, beban
berat ada di inference YOLO — pendekatan yang dipilih adalah: tetap sinkron pada
DB, lalu memindahkan operasi berat (file I/O & inference) ke thread pool lewat
`asyncio.to_thread` di router (#11). Connection pool dikonfigurasi eksplisit agar
tahan beban konkuren.
"""
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings
from app.logging_config import get_logger


logger = get_logger(__name__)


# Engine MySQL dengan pool yang dikonfigurasi eksplisit (#10).
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,                      # cegah koneksi expired
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk semua model SQLAlchemy
Base = declarative_base()


def get_db():
    """Dependency FastAPI untuk inject session DB ke route."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db() -> None:
    """
    Tunggu database siap saat startup dengan exponential backoff (#49).

    Berguna ketika backend dan MySQL start bersamaan (mis. docker-compose) dan
    DB belum menerima koneksi.
    """
    retries = settings.DB_CONNECT_RETRIES
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Koneksi database OK", extra={"attempt": attempt})
            return
        except OperationalError as exc:
            last_error = exc
            if attempt >= retries:
                break
            delay = min(2 ** attempt, 30)
            logger.warning(
                "Database belum siap, mencoba lagi",
                extra={"attempt": attempt + 1, "max": retries, "delay_s": delay},
            )
            time.sleep(delay)

    logger.error("Gagal terhubung ke database setelah beberapa percobaan")
    raise RuntimeError(
        f"Tidak bisa terhubung ke database setelah {retries} percobaan"
    ) from last_error


def check_db_health() -> bool:
    """Cek cepat apakah DB merespon (dipakai endpoint /health) (#8)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001 — health check tidak boleh melempar
        logger.warning("Health check DB gagal", extra={"error": str(exc)})
        return False
