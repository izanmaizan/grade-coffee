"""
Seeder data awal untuk tabel grade_prices.
Dijalankan otomatis pada startup pertama (jika tabel kosong).

Harga di bawah hanya CONTOH simulasi (Rupiah per gram).
Sesuaikan dengan harga pasar Anda lewat menu "Harga" di frontend.
"""
from sqlalchemy.orm import Session

from app.models.db_models import GradePrice


# ==================================================
# Data awal grade — bisa diedit lewat UI nanti
# ==================================================
DEFAULT_GRADES = [
    {
        "grade_code": "GRADE_1",
        "grade_name": "Specialty Grade",
        "description": (
            "Kualitas tertinggi (SCA Specialty). Maksimum 5 defect per 350g, "
            "tidak ada primary defect. Cocok untuk specialty coffee shop."
        ),
        "price_per_gram": 180.0,   # Rp 180 / gram → Rp 180.000 / kg
        "min_defects": 0,
        "max_defects": 5,
        "color": "#10b981",  # emerald-500
    },
    {
        "grade_code": "GRADE_2",
        "grade_name": "Premium Grade",
        "description": (
            "Kualitas premium. 6-8 defect per 350g. "
            "Cocok untuk komersial high-end / kafe menengah-atas."
        ),
        "price_per_gram": 130.0,   # Rp 130 / gram → Rp 130.000 / kg
        "min_defects": 6,
        "max_defects": 8,
        "color": "#3b82f6",  # blue-500
    },
    {
        "grade_code": "GRADE_3",
        "grade_name": "Exchange Grade",
        "description": (
            "Kualitas pasar / commercial. 9-23 defect per 350g. "
            "Standar perdagangan kopi umum (commodity grade)."
        ),
        "price_per_gram": 85.0,    # Rp 85 / gram → Rp 85.000 / kg
        "min_defects": 9,
        "max_defects": 23,
        "color": "#f59e0b",  # amber-500
    },
    {
        "grade_code": "GRADE_4",
        "grade_name": "Below Standard",
        "description": (
            "Kualitas di bawah standar. >23 defect per 350g. "
            "Hanya cocok untuk blending kopi murah atau industri."
        ),
        "price_per_gram": 50.0,    # Rp 50 / gram → Rp 50.000 / kg
        "min_defects": 24,
        "max_defects": None,
        "color": "#ef4444",  # red-500
    },
]


def seed_grades(db: Session) -> int:
    """
    Insert default grades jika tabel grade_prices masih kosong.
    Returns: jumlah row yang ditambahkan.
    """
    existing = db.query(GradePrice).count()
    if existing > 0:
        return 0

    inserted = 0
    for data in DEFAULT_GRADES:
        db.add(GradePrice(**data))
        inserted += 1

    db.commit()
    return inserted