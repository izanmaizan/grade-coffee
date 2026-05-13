"""
Endpoint pengelolaan harga grade:
  GET    /api/prices       → list semua harga grade
  GET    /api/prices/{id}  → detail satu grade
  POST   /api/prices       → tambah grade baru
  PUT    /api/prices/{id}  → update harga / properti grade
  DELETE /api/prices/{id}  → hapus grade
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import GradePrice
from app.models.schemas import (
    GradePriceCreate,
    GradePriceUpdate,
    GradePriceResponse,
)


router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("", response_model=list[GradePriceResponse])
def list_prices(db: Session = Depends(get_db)):
    """Ambil semua grade, urut berdasarkan min_defects (Grade 1 → 4)."""
    return db.query(GradePrice).order_by(GradePrice.min_defects.asc()).all()


@router.get("/{grade_id}", response_model=GradePriceResponse)
def get_price(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradePrice).filter(GradePrice.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade tidak ditemukan")
    return grade


@router.post("", response_model=GradePriceResponse, status_code=201)
def create_price(payload: GradePriceCreate, db: Session = Depends(get_db)):
    # Cek duplikasi grade_code
    existing = (
        db.query(GradePrice)
        .filter(GradePrice.grade_code == payload.grade_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Grade dengan kode '{payload.grade_code}' sudah ada",
        )

    grade = GradePrice(**payload.model_dump())
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade


@router.put("/{grade_id}", response_model=GradePriceResponse)
def update_price(
    grade_id: int,
    payload: GradePriceUpdate,
    db: Session = Depends(get_db),
):
    grade = db.query(GradePrice).filter(GradePrice.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade tidak ditemukan")

    # Update hanya field yang dikirim
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(grade, field, value)

    db.commit()
    db.refresh(grade)
    return grade


@router.delete("/{grade_id}", status_code=204)
def delete_price(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(GradePrice).filter(GradePrice.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade tidak ditemukan")
    db.delete(grade)
    db.commit()
    return None