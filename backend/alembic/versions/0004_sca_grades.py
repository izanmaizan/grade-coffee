"""switch grade_prices to SCA 3-tier

Ganti isi grade_prices dari SNI 5-grade ke SCA 3-tier (Specialty/Premium/
Commercial). Ambang = full defect equivalent per 300g. Tidak memengaruhi
analysis_history (grade_code disimpan sebagai string).

Revision ID: 0004_sca_grades
Revises: 0003_sni_grades
Create Date: 2026-06-06
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0004_sca_grades"
down_revision: Union[str, None] = "0003_sni_grades"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, name, description, price, min, max, color)
SCA_GRADES = [
    ("GRADE_1", "Specialty Grade", "Kualitas tertinggi (SCA, skor 80+). Toleransi cacat 0-3 per 300g.", 180.0, 0, 3, "#10b981"),
    ("GRADE_2", "Premium Grade", "Kualitas tinggi (SCA, skor 70-80). Cacat 4-12 per 300g.", 130.0, 4, 12, "#3b82f6"),
    ("GRADE_3", "Commercial Grade", "Kualitas komersial (SCA, skor <70). Cacat 13+ per 300g.", 85.0, 13, None, "#f59e0b"),
]

SNI_GRADES = [
    ("GRADE_1", "Grade 1 (Mutu 1)", "Mutu terbaik (SNI). Nilai cacat maksimum 11 per 300g.", 180.0, 0, 11, "#10b981"),
    ("GRADE_2", "Grade 2 (Mutu 2)", "Kualitas premium. Nilai cacat 12-25 per 300g.", 130.0, 12, 25, "#3b82f6"),
    ("GRADE_3", "Grade 3 (Mutu 3)", "Kualitas komersial. Nilai cacat 26-44 per 300g.", 90.0, 26, 44, "#f59e0b"),
    ("GRADE_4", "Grade 4 (Mutu 4)", "Di bawah standar. Nilai cacat 45-150 per 300g.", 60.0, 45, 150, "#f97316"),
    ("GRADE_5", "Grade 5 (Mutu 5)", "Mutu terendah. Nilai cacat 151+ per 300g.", 40.0, 151, None, "#ef4444"),
]


def _replace_grades(rows) -> None:
    op.execute("DELETE FROM grade_prices")
    for code, name, desc, price, mn, mx, color in rows:
        max_sql = "NULL" if mx is None else str(mx)
        desc_sql = desc.replace("'", "''")
        op.execute(
            "INSERT INTO grade_prices "
            "(grade_code, grade_name, description, price_per_gram, min_defects, "
            " max_defects, color, created_at, updated_at) VALUES "
            f"('{code}', '{name}', '{desc_sql}', {price}, {mn}, {max_sql}, "
            f"'{color}', NOW(), NOW())"
        )


def upgrade() -> None:
    _replace_grades(SCA_GRADES)


def downgrade() -> None:
    _replace_grades(SNI_GRADES)
