"""
Schema Pydantic untuk validasi request/response API.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==================================================
# GRADE PRICE SCHEMAS
# ==================================================
class GradePriceBase(BaseModel):
    grade_code: str = Field(..., min_length=1, max_length=20)
    grade_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price_per_gram: float = Field(..., ge=0)
    min_defects: int = Field(..., ge=0)
    max_defects: Optional[int] = Field(None, ge=0)
    color: str = Field("#808080", max_length=20)


class GradePriceCreate(GradePriceBase):
    """Untuk POST /api/prices"""
    pass


class GradePriceUpdate(BaseModel):
    """Untuk PUT /api/prices/{id} — semua field optional."""
    grade_name: Optional[str] = None
    description: Optional[str] = None
    price_per_gram: Optional[float] = Field(None, ge=0)
    min_defects: Optional[int] = Field(None, ge=0)
    max_defects: Optional[int] = Field(None, ge=0)
    color: Optional[str] = None


class GradePriceResponse(GradePriceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================================================
# ANALYSIS SCHEMAS
# ==================================================
class AnalyzeRequest(BaseModel):
    """Form data: weight_gram dikirim bersama file."""
    weight_gram: float = Field(350.0, gt=0, description="Berat sampel dalam gram")


class DetectionItem(BaseModel):
    """Satu objek hasil deteksi YOLO."""
    class_name: str
    confidence: float
    bbox: list[float]  # [x1, y1, x2, y2]


class AnalyzeResponse(BaseModel):
    """Response setelah analisis selesai."""
    id: int
    image_filename: str
    result_image_url: str
    weight_gram: float
    total_defects: int
    defects_per_350g: float
    detection_summary: Dict[str, int]
    detections: list[DetectionItem]

    grade_code: str
    grade_name: str
    grade_color: str
    grade_description: Optional[str] = None

    price_per_gram: float
    total_price: float
    confidence_avg: float
    processing_time_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================================================
# HISTORY SCHEMAS
# ==================================================
class HistoryItem(BaseModel):
    id: int
    image_filename: str
    result_image_path: Optional[str]
    weight_gram: float
    total_defects: int
    defects_per_350g: float
    grade_code: str
    grade_name: str
    price_per_gram: float
    total_price: float
    detection_summary: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[HistoryItem]


# ==================================================
# STATS / DASHBOARD
# ==================================================
class StatsResponse(BaseModel):
    total_analyses: int
    total_weight_kg: float
    total_revenue: float
    grade_distribution: Dict[str, int]
    recent_count_7days: int