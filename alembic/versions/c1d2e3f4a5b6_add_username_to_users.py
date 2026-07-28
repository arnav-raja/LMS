"""add username to users

Revision ID: c1d2e3f4a5b6
Revises: ed2e4cddc7a3
Create Date: 2026-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'ed2e4cddc7a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Added nullable first so existing rows do not break the migration;
    # backfill existing users (e.g. from their email prefix) before
    # tightening this to NOT NULL in a follow-up deploy step.
    op.add_column(
        'users',
        sa.Column('username', sa.String(length=50), nullable=True)
    )
    op.create_unique_constraint(
        'uq_users_username',
        'users',
        ['username']
    )
    op.create_index(
        op.f('ix_users_username'),
        'users',
        ['username'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.drop_column('users', 'username')
