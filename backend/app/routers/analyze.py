"""
Endpoint analisis gambar green coffee bean:
  POST /api/analyze       → upload gambar + berat → hasil deteksi & grade
  GET  /api/analyze/status → status model
"""
import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.logging_config import get_logger
from app.models.db_models import AnalysisHistory
from app.models.schemas import AnalyzeResponse, DetectionItem
from app.rate_limit import limiter
from app.services import grade_cache, storage
from app.services.detector import BeanDetector, calculate_defect_value
from app.services.storage import InvalidImageError


logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])


@router.post("", response_model=AnalyzeResponse)
@limiter.limit(settings.RATE_LIMIT_ANALYZE)
async def analyze_image(
    request: Request,
    image: UploadFile = File(..., description="Gambar green coffee bean"),
    weight_gram: float = Form(350.0, gt=0, le=10000, description="Berat sampel (gram)"),
    db: Session = Depends(get_db),
):
    """
    Upload gambar + masukkan berat sampel → dapatkan grade & total harga.

    Flow:
        1. Baca & batasi ukuran file (#4)
        2. Validasi konten + kompres + simpan (#4, #39)
        3. Jalankan YOLO detection di thread pool dengan timeout (#11, #52)
        4. Hitung grade (presisi Decimal)
        5. Ambil harga dari cache/DB (#32)
        6. Simpan history & kembalikan hasil
    """
    # 1) Baca file dengan batas ukuran (streaming, hindari muat file raksasa) (#4)
    max_bytes = settings.max_upload_bytes
    chunks = []
    size = 0
    while True:
        chunk = await image.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Ukuran file melebihi batas {settings.MAX_UPLOAD_MB} MB",
            )
        chunks.append(chunk)
    raw = b"".join(chunks)
    if not raw:
        raise HTTPException(status_code=400, detail="File kosong")

    # 2) Validasi konten + kompres + simpan (di thread, karena Pillow blocking)
    try:
        saved_path = await asyncio.to_thread(storage.validate_and_save_upload, raw)
    except InvalidImageError as exc:
        raise HTTPException(status_code=415, detail=str(exc))

    # 3) Detection
    detector = BeanDetector()
    if not detector.is_ready():
        storage.delete_files(str(saved_path))
        raise HTTPException(
            status_code=503,
            detail=(
                "Model YOLO belum tersedia. Lakukan pelatihan terlebih dahulu, "
                "lalu letakkan file best.pt di backend/weights/best.pt"
            ),
        )

    try:
        # Inference berat dipindah ke thread pool + diberi timeout (#11, #52)
        result, result_image_path, elapsed_ms = await asyncio.wait_for(
            asyncio.to_thread(detector.detect, str(saved_path)),
            timeout=settings.INFERENCE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        storage.delete_files(str(saved_path))
        logger.error("Inference timeout", extra={"file": saved_path.name})
        raise HTTPException(status_code=504, detail="Deteksi melebihi batas waktu")
    except Exception as exc:  # noqa: BLE001 — dibungkus jadi 500 + dicatat penuh
        storage.delete_files(str(saved_path))
        logger.error("Deteksi gagal", exc_info=exc)
        raise HTTPException(status_code=500, detail="Deteksi gagal diproses")

    # 4) Hitung NILAI CACAT berbobot SNI (normalisasi ke berat acuan, mis. 300g)
    dv = calculate_defect_value(result["class_counts"], weight_gram)

    # 5) Tentukan GRADE dari ambang di DB (data-driven, bisa diatur via UI Harga)
    grade = grade_cache.find_grade_for_value(db, dv.defect_value_per_ref)
    if not grade:
        raise HTTPException(
            status_code=500,
            detail=(
                "Belum ada konfigurasi grade di database. "
                "Jalankan seeder/migrasi grade_prices terlebih dahulu."
            ),
        )
    grade_code = grade.grade_code
    defects_per_350g = dv.defect_value_per_ref

    total_price = round(weight_gram * grade.price_per_gram, 2)

    # 6) Simpan ke history
    history = AnalysisHistory(
        image_filename=image.filename or saved_path.name,
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
    return AnalyzeResponse(
        id=history.id,
        image_filename=history.image_filename,
        result_image_url=storage.build_url(result_image_path) or "",
        weight_gram=weight_gram,
        total_defects=result["total_defects"],
        defects_per_350g=defects_per_350g,
        detection_summary=result["class_counts"],
        detections=[DetectionItem(**d) for d in result["detections"]],
        defect_value=dv.defect_value_per_ref,
        reference_gram=dv.reference_gram,
        defect_berat=dv.berat_count,
        defect_ringan=dv.ringan_count,
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
        "model_version": detector.model_version,
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
        "model_version": detector.model_version,
    }
