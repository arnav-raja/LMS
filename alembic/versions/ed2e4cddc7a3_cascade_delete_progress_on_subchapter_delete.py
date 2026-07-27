"""cascade-delete progress rows when their subchapter is deleted

Revision ID: ed2e4cddc7a3
Revises: 76fc7ab18489
Create Date: 2026-07-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ed2e4cddc7a3'
down_revision: Union[str, Sequence[str], None] = '76fc7ab18489'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The original FK had no ON DELETE behaviour, so deleting a subchapter
    # that still had progress recorded against it would fail outright.
    # This is a safety net: app code is expected to clean up progress
    # explicitly, but the database will no longer block or silently
    # allow an inconsistent delete either way.
    op.drop_constraint(
        'progress_subchapter_id_fkey',
        'progress',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'progress_subchapter_id_fkey',
        'progress',
        'subchapters',
        ['subchapter_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'progress_subchapter_id_fkey',
        'progress',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'progress_subchapter_id_fkey',
        'progress',
        'subchapters',
        ['subchapter_id'],
        ['id']
    )
