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
# Ambang = FULL DEFECT EQUIVALENT per berat acuan (SCA, per 300g). Harga = contoh,
# sesuaikan via halaman Harga. Penentuan grade data-driven dari min/max_defects.
DEFAULT_GRADES = [
    {
        "grade_code": "GRADE_1",
        "grade_name": "Specialty Grade",
        "description": (
            "Kualitas tertinggi (SCA, skor 80+). Toleransi cacat 0–3 per 300g. "
            "Rasa bersih & kompleks. Cocok untuk specialty coffee shop / ekspor."
        ),
        "price_per_gram": 180.0,
        "min_defects": 0,
        "max_defects": 3,
        "color": "#10b981",  # emerald-500
    },
    {
        "grade_code": "GRADE_2",
        "grade_name": "Premium Grade",
        "description": (
            "Kualitas tinggi (SCA, skor 70–80). Cacat 4–12 per 300g. "
            "Konsisten & seimbang. Cocok untuk kafe / home brewing premium."
        ),
        "price_per_gram": 130.0,
        "min_defects": 4,
        "max_defects": 12,
        "color": "#3b82f6",  # blue-500
    },
    {
        "grade_code": "GRADE_3",
        "grade_name": "Commercial Grade",
        "description": (
            "Kualitas komersial (SCA, skor <70). Cacat 13+ per 300g. "
            "Profil standar (cokelat/kacang), untuk konsumsi harian / blend."
        ),
        "price_per_gram": 85.0,
        "min_defects": 13,
        "max_defects": None,
        "color": "#f59e0b",  # amber-500
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