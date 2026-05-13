"""
Endpoint analisis gambar green coffee bean:
  POST /api/analyze       → upload gambar + berat → hasil deteksi & grade
  GET  /api/analyze/{id}  → ambil detail satu analisis
"""
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.db_models import AnalysisHistory, GradePrice
from app.models.schemas import AnalyzeResponse, DetectionItem
from app.services.detector import BeanDetector, calculate_grade


router = APIRouter(prefix="/api/analyze", tags=["analyze"])


ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@router.post("", response_model=AnalyzeResponse)
async def analyze_image(
    image: UploadFile = File(..., description="Gambar green coffee bean"),
    weight_gram: float = Form(350.0, gt=0, description="Berat sampel (gram)"),
    db: Session = Depends(get_db),
):
    """
    Upload gambar + masukkan berat sampel → dapatkan grade & total harga.

    Flow:
        1. Validasi & simpan gambar
        2. Jalankan YOLO detection
        3. Hitung grade berdasarkan defect / 350g
        4. Ambil harga dari DB sesuai grade
        5. Simpan history ke DB
        6. Return hasil lengkap
    """
    # 1) Validasi ekstensi file
    ext = Path(image.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Format gambar tidak didukung. Gunakan: {', '.join(ALLOWED_EXTS)}",
        )

    # 2) Simpan file ke uploads/
    safe_name = f"{uuid.uuid4().hex[:12]}_{Path(image.filename).name}"
    saved_path = settings.upload_full_path / safe_name
    with saved_path.open("wb") as f:
        shutil.copyfileobj(image.file, f)

    # 3) Detection
    detector = BeanDetector()
    if not detector.is_ready():
        raise HTTPException(
            status_code=503,
            detail=(
                "Model YOLO belum tersedia. Lakukan pelatihan terlebih dahulu, "
                "lalu letakkan file best.pt di backend/weights/best.pt"
            ),
        )

    try:
        result, result_image_path, elapsed_ms = detector.detect(str(saved_path))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Deteksi gagal: {exc}")

    # 4) Hitung grade
    grade_code, defects_per_350g = calculate_grade(
        result["total_defects"], weight_gram
    )

    # 5) Ambil harga dari database
    grade = db.query(GradePrice).filter(GradePrice.grade_code == grade_code).first()
    if not grade:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Konfigurasi grade {grade_code} tidak ditemukan di database. "
                "Jalankan seeder grade_prices terlebih dahulu."
            ),
        )

    total_price = round(weight_gram * grade.price_per_gram, 2)

    # 6) Simpan ke history
    history = AnalysisHistory(
        image_filename=image.filename or safe_name,
        image_path=str(saved_path),
        result_image_path=result_image_path,
        weight_gram=weight_gram,
        total_defects=result["total_defects"],
        defects_per_350g=defects_per_350g,
        detection_summary=result["class_counts"],
        grade_code=grade_code,
        grade_name=grade.grade_name,
        price_per_gram=grade.price_per_gram,
        total_price=total_price,
        confidence_avg=result["confidence_avg"],
        processing_time_ms=elapsed_ms,
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    # 7) Build response
    result_filename = Path(result_image_path).name if result_image_path else ""
    return AnalyzeResponse(
        id=history.id,
        image_filename=history.image_filename,
        result_image_url=f"/uploads/{result_filename}" if result_filename else "",
        weight_gram=weight_gram,
        total_defects=result["total_defects"],
        defects_per_350g=defects_per_350g,
        detection_summary=result["class_counts"],
        detections=[DetectionItem(**d) for d in result["detections"]],
        grade_code=grade_code,
        grade_name=grade.grade_name,
        grade_color=grade.color,
        grade_description=grade.description,
        price_per_gram=grade.price_per_gram,
        total_price=total_price,
        confidence_avg=result["confidence_avg"],
        processing_time_ms=elapsed_ms,
        created_at=history.created_at,
    )


@router.post("/reload-model", tags=["admin"])
def reload_model():
    """Reload model setelah selesai re-training (tanpa restart server)."""
    detector = BeanDetector()
    detector.reload()
    return {
        "status": "ok",
        "ready": detector.is_ready(),
        "device": detector.device,
        "model_path": str(detector.model_path),
    }


@router.get("/status")
def model_status():
    """Cek status model — apakah siap dipakai inference?"""
    detector = BeanDetector()
    return {
        "ready": detector.is_ready(),
        "device": detector.device,
        "model_path": str(detector.model_path),
        "model_exists": detector.model_path.exists(),
    }