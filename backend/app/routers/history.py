"""
Endpoint history & statistik:
  GET    /api/history          → list riwayat (pagination)
  GET    /api/history/{id}     → detail satu analisis
  DELETE /api/history/{id}     → hapus satu entry
  GET    /api/history/stats/summary → ringkasan untuk dashboard
"""
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import AnalysisHistory
from app.models.schemas import HistoryItem, HistoryListResponse, StatsResponse


router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    grade_code: str | None = Query(None, description="Filter berdasarkan grade"),
    db: Session = Depends(get_db),
):
    """Ambil riwayat analisis dengan pagination, terbaru di atas."""
    query = db.query(AnalysisHistory)
    if grade_code:
        query = query.filter(AnalysisHistory.grade_code == grade_code)

    total = query.count()
    items = (
        query.order_by(AnalysisHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert path file menjadi URL untuk frontend
    results = []
    for item in items:
        result_filename = (
            Path(item.result_image_path).name if item.result_image_path else None
        )
        results.append(
            HistoryItem(
                id=item.id,
                image_filename=item.image_filename,
                result_image_path=(
                    f"/uploads/{result_filename}" if result_filename else None
                ),
                weight_gram=item.weight_gram,
                total_defects=item.total_defects,
                defects_per_350g=item.defects_per_350g,
                grade_code=item.grade_code,
                grade_name=item.grade_name,
                price_per_gram=item.price_per_gram,
                total_price=item.total_price,
                detection_summary=item.detection_summary,
                created_at=item.created_at,
            )
        )

    return HistoryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=results,
    )


@router.get("/stats/summary", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Statistik untuk header dashboard / halaman history."""
    total = db.query(func.count(AnalysisHistory.id)).scalar() or 0
    total_weight_g = db.query(func.sum(AnalysisHistory.weight_gram)).scalar() or 0.0
    total_revenue = db.query(func.sum(AnalysisHistory.total_price)).scalar() or 0.0

    # Distribusi grade
    grade_rows = (
        db.query(AnalysisHistory.grade_code, func.count(AnalysisHistory.id))
        .group_by(AnalysisHistory.grade_code)
        .all()
    )
    grade_dist = {code: count for code, count in grade_rows}

    # Hitungan 7 hari terakhir
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = (
        db.query(func.count(AnalysisHistory.id))
        .filter(AnalysisHistory.created_at >= week_ago)
        .scalar()
        or 0
    )

    return StatsResponse(
        total_analyses=total,
        total_weight_kg=round(total_weight_g / 1000.0, 3),
        total_revenue=round(float(total_revenue), 2),
        grade_distribution=grade_dist,
        recent_count_7days=recent,
    )


@router.get("/{history_id}", response_model=HistoryItem)
def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    item = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")

    result_filename = (
        Path(item.result_image_path).name if item.result_image_path else None
    )
    return HistoryItem(
        id=item.id,
        image_filename=item.image_filename,
        result_image_path=(
            f"/uploads/{result_filename}" if result_filename else None
        ),
        weight_gram=item.weight_gram,
        total_defects=item.total_defects,
        defects_per_350g=item.defects_per_350g,
        grade_code=item.grade_code,
        grade_name=item.grade_name,
        price_per_gram=item.price_per_gram,
        total_price=item.total_price,
        detection_summary=item.detection_summary,
        created_at=item.created_at,
    )


@router.delete("/{history_id}", status_code=204)
def delete_history(history_id: int, db: Session = Depends(get_db)):
    item = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")

    # Optional: hapus file gambar fisik juga
    for path_str in [item.image_path, item.result_image_path]:
        if path_str:
            try:
                Path(path_str).unlink(missing_ok=True)
            except Exception:
                pass

    db.delete(item)
    db.commit()
    return None