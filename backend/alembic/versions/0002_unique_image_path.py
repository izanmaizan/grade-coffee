"""add unique constraint on analysis_history.image_path

Cegah dua record menunjuk file fisik yang sama (#30).

Revision ID: 0002_unique_image_path
Revises: 0001_initial
Create Date: 2026-06-05
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0002_unique_image_path"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_analysis_history_image_path", "analysis_history", ["image_path"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_analysis_history_image_path", "analysis_history", type_="unique"
    )
