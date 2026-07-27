"""move subchapter configuration to chapters

Revision ID: b387d9ac5abb
Revises: a43198a5ebae
Create Date: 2026-07-24
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision = "b387d9ac5abb"
down_revision = "a43198a5ebae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chapters",
        sa.Column(
            "num_subchapters",
            sa.Integer(),
            nullable=False,
            server_default="0"
        )
    )

    op.drop_column(
        "courses",
        "num_subchapters"
    )


def downgrade() -> None:
    op.add_column(
        "courses",
        sa.Column(
            "num_subchapters",
            sa.Integer(),
            nullable=False,
            server_default="0"
        )
    )

    op.drop_column(
        "chapters",
        "num_subchapters"
    )