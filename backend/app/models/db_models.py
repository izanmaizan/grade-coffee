"""
Model SQLAlchemy untuk database green_bean_grading.

Tabel:
  - grade_prices    → harga per gram tiap grade (Grade 1-4)
  - analysis_history → riwayat analisis gambar
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    JSON,
)

from app.database import Base


class GradePrice(Base):
    """
    Harga per gram untuk tiap grade green coffee bean.

    Standar grading mengikuti SCA (Specialty Coffee Association):
      - Grade 1 (Specialty)     : 0-5  defects per 350g
      - Grade 2 (Premium)       : 6-8  defects per 350g
      - Grade 3 (Exchange)      : 9-23 defects per 350g
      - Grade 4 (Below Standard): >23  defects per 350g
    """
    __tablename__ = "grade_prices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grade_code = Column(String(20), unique=True, nullable=False, index=True)
    grade_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price_per_gram = Column(Float, nullable=False, default=0.0)  # Rupiah per gram
    min_defects = Column(Integer, nullable=False, default=0)
    max_defects = Column(Integer, nullable=True)  # None = unlimited
    color = Column(String(20), nullable=False, default="#808080")  # warna untuk UI
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class AnalysisHistory(Base):
    """
    Riwayat semua analisis yang pernah dilakukan.

    Menyimpan ringkasan deteksi + perhitungan harga.
    """
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_filename = Column(String(255), nullable=False)
    image_path = Column(String(512), nullable=False)
    result_image_path = Column(String(512), nullable=True)

    # Berat sampel yang diuji (gram)
    weight_gram = Column(Float, nullable=False, default=350.0)

    # Hasil deteksi
    total_defects = Column(Integer, nullable=False, default=0)
    defects_per_350g = Column(Float, nullable=False, default=0.0)
    detection_summary = Column(JSON, nullable=True)  # {"broken": 3, "fade": 1, ...}

    # Hasil grading
    grade_code = Column(String(20), nullable=False)
    grade_name = Column(String(100), nullable=False)
    price_per_gram = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)  # weight * price/g

    # Metadata
    confidence_avg = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)