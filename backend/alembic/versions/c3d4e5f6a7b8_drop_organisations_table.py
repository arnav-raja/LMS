"""drop organisations table

Revision ID: c3d4e5f6a7b8
Revises: b8c9d0e1f2a3
Create Date: 2026-07-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index('ix_organisations_custom_domain', table_name='organisations')
    op.drop_table('organisations')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'organisations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('custom_domain', sa.String(length=255), nullable=True),
        sa.Column('verification_token', sa.String(length=64), nullable=True),
        sa.Column('domain_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('custom_domain', name='uq_organisations_custom_domain')
    )
    op.create_index(
        'ix_organisations_custom_domain',
        'organisations',
        ['custom_domain'],
        unique=False
    )
