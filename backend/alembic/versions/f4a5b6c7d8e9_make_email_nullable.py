"""make users.email nullable

Revision ID: f4a5b6c7d8e9
Revises: d2e3f4a5b6c7
Create Date: 2026-07-28 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, Sequence[str], None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Username is now the required, primary identifier for signing in and
    for creating an account from the Students page — email becomes an
    optional contact field. The existing unique constraint on email is
    untouched; Postgres already treats multiple NULLs in a unique column
    as distinct, so several students can have no email on file at once.
    """
    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=200),
        nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=200),
        nullable=False
    )
