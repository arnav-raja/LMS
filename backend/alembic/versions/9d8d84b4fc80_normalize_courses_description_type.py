"""normalize courses description type

Revision ID: 9d8d84b4fc80
Revises: 1252d54a689b
Create Date: 2026-07-25 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d8d84b4fc80'
down_revision: Union[str, Sequence[str], None] = '1252d54a689b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('courses', 'description',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('courses', 'description',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               nullable=True)
