"""
Cache ringan untuk data harga grade (#32).

Harga grade jarang berubah tetapi dibaca pada setiap analisis. Cache in-memory
dengan TTL menekan beban query DB. Cache otomatis di-invalidate saat ada
perubahan via endpoint prices (lihat invalidate()).
"""
import threading
import time
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.db_models import GradePrice
from app.logging_config import get_logger


logger = get_logger(__name__)

_TTL_SECONDS = 300  # 5 menit
_lock = threading.Lock()
_cache: Dict[str, GradePrice] = {}
_loaded_at: float = 0.0


def _is_fresh() -> bool:
    return _cache and (time.time() - _loaded_at) < _TTL_SECONDS


def _refresh_if_stale(db: Session) -> None:
    global _loaded_at
    if not _is_fresh():
        rows = db.query(GradePrice).all()
        _cache.clear()
        _cache.update({g.grade_code: g for g in rows})
        _loaded_at = time.time()
        logger.debug("Cache grade di-refresh", extra={"count": len(_cache)})


def get_grade(db: Session, grade_code: str) -> Optional[GradePrice]:
    """Ambil satu grade berdasarkan kode, memakai cache bila masih segar."""
    with _lock:
        _refresh_if_stale(db)
        return _cache.get(grade_code)


def find_grade_for_value(db: Session, defect_value: float) -> Optional[GradePrice]:
    """
    Cari grade yang rentang [min_defects, max_defects]-nya memuat nilai cacat (#data-driven).

    Ambang grade sepenuhnya dari DB (tabel grade_prices) sehingga bisa diatur lewat
    halaman Harga — mendukung skema SNI 5-grade, SCA 3-tier, atau skema kustom
    tanpa mengubah kode. Grade diurut menaik berdasarkan min_defects; dipilih grade
    pertama yang max_defects-nya >= nilai (max_defects None = tak terbatas).
    """
    with _lock:
        _refresh_if_stale(db)
        grades = sorted(_cache.values(), key=lambda g: g.min_defects)

    if not grades:
        return None

    for grade in grades:
        upper = grade.max_defects
        if defect_value >= grade.min_defects and (upper is None or defect_value <= upper):
            return grade
    # Di atas semua ambang → kembalikan grade terburuk (max_defects terbesar/None)
    return grades[-1]


def invalidate() -> None:
    """Kosongkan cache (dipanggil setelah create/update/delete harga)."""
    with _lock:
        _cache.clear()
        logger.debug("Cache grade di-invalidate")
