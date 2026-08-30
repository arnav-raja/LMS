"""finish the username constraints the models already assume

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-30 12:30:00.000000

Migration c1d2e3f4a5b6 added `users.username` as nullable and said:

    backfill existing users (e.g. from their email prefix) before
    tightening this to NOT NULL in a follow-up deploy step.

That follow-up was never written, so the model has been declaring
`nullable=False, unique=True, index=True` while the database allowed NULL
and carried a *non-unique* index next to a separate unique constraint.
Everything worked because SQLAlchemy enforced it on the Python side; the
database itself would have accepted a user with no username at all.

This is that follow-up. It backfills, then makes the database agree with
the models.

The backfill takes the part of the email before the '@' where that is
free, and falls back to `<base>_<id>` otherwise, which cannot collide
because ids are unique. Any account it has to fall back on is worth
renaming by hand afterwards:

    SELECT id, name, email, username FROM users WHERE username LIKE '%\\_%';
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BACKFILL_USERNAMES = """
WITH candidates AS (
    SELECT id,
           COALESCE(NULLIF(split_part(email, '@', 1), ''), 'user') AS base
      FROM users
     WHERE username IS NULL
),
numbered AS (
    SELECT c.id,
           c.base,
           ROW_NUMBER() OVER (PARTITION BY c.base ORDER BY c.id) AS position,
           EXISTS (
               SELECT 1 FROM users taken WHERE taken.username = c.base
           ) AS already_taken
      FROM candidates c
)
UPDATE users
   SET username = CASE
                    WHEN numbered.position = 1 AND NOT numbered.already_taken
                    THEN numbered.base
                    ELSE numbered.base || '_' || users.id
                  END
  FROM numbered
 WHERE users.id = numbered.id
"""


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(BACKFILL_USERNAMES)

    op.alter_column(
        'users',
        'username',
        existing_type=sa.String(length=50),
        nullable=False,
    )

    # The model expresses uniqueness through the index itself
    # (unique=True, index=True), so the standalone constraint is redundant
    # and the index has to become unique in its place.
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.create_index(
        op.f('ix_users_username'),
        'users',
        ['username'],
        unique=True,
    )

    # Declared on the model as index=True but never created. Redundant with
    # the primary key on PostgreSQL, and kept only so the schema matches
    # what the models describe — see tests/test_migrations.py.
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_id'), table_name='users')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.create_index(
        op.f('ix_users_username'),
        'users',
        ['username'],
        unique=False,
    )
    op.create_unique_constraint('uq_users_username', 'users', ['username'])

    op.alter_column(
        'users',
        'username',
        existing_type=sa.String(length=50),
        nullable=True,
    )
