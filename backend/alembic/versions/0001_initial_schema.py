"""initial schema

Skema awal lengkap: grade_prices + analysis_history.
Migration ini bisa membangun database dari nol (deployment baru / docker).

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grade_prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("grade_code", sa.String(length=20), nullable=False),
        sa.Column("grade_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_per_gram", sa.Float(), nullable=False),
        sa.Column("min_defects", sa.Integer(), nullable=False),
        sa.Column("max_defects", sa.Integer(), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grade_code"),
    )
    op.create_index(
        op.f("ix_grade_prices_grade_code"), "grade_prices", ["grade_code"]
    )
    op.create_index(op.f("ix_grade_prices_id"), "grade_prices", ["id"])

    op.create_table(
        "analysis_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("image_filename", sa.String(length=255), nullable=False),
        sa.Column("image_path", sa.String(length=512), nullable=False),
        sa.Column("result_image_path", sa.String(length=512), nullable=True),
        sa.Column("weight_gram", sa.Float(), nullable=False),
        sa.Column("total_defects", sa.Integer(), nullable=False),
        sa.Column("defects_per_350g", sa.Float(), nullable=False),
        sa.Column("detection_summary", sa.JSON(), nullable=True),
        sa.Column("grade_code", sa.String(length=20), nullable=False),
        sa.Column("grade_name", sa.String(length=100), nullable=False),
        sa.Column("price_per_gram", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("confidence_avg", sa.Float(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_history_id"), "analysis_history", ["id"])
    # index created_at untuk query history yang selalu sort desc (#21)
    op.create_index(
        op.f("ix_analysis_history_created_at"), "analysis_history", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_history_created_at"), table_name="analysis_history")
    op.drop_index(op.f("ix_analysis_history_id"), table_name="analysis_history")
    op.drop_table("analysis_history")
    op.drop_index(op.f("ix_grade_prices_id"), table_name="grade_prices")
    op.drop_index(op.f("ix_grade_prices_grade_code"), table_name="grade_prices")
    op.drop_table("grade_prices")
