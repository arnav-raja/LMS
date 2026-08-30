"""constrain role and status, and store timestamps as timestamptz

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-30 12:00:00.000000

Two changes that both close a gap between what the code assumes and what
the database actually enforces.

1. `users.role` and `courses.status` were unconstrained text. The API let
   an admin POST any string as a role, and nothing stopped it reaching the
   table — an account with role 'wizard' would simply never match either
   branch of the permission checks. Departments and seniorities already had
   CHECK constraints; these two were the ones that had been missed.

2. Every timestamp column was `TIMESTAMP WITHOUT TIME ZONE`, written from
   `datetime.utcnow()`. The values were UTC, but nothing recorded that, so
   anything reading them had to already know. They are converted in place
   with `AT TIME ZONE 'UTC'`, which is correct precisely because every
   existing value was written as UTC.

If the first step fails, the database holds a role or status this
application never writes. Find them with:

    SELECT DISTINCT role FROM users;
    SELECT DISTINCT status FROM courses;

and correct them before re-running.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.constants import CourseStatus
from app.constants import Role
from app.constants import sql_value_list


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column) for every timestamp the application writes.
TIMESTAMP_COLUMNS = [
    ("progress", "completed_at"),
    ("certificates", "issued_at"),
    ("quiz_attempts", "submitted_at"),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        'ck_users_role_valid',
        'users',
        f"role IN {sql_value_list(Role)}"
    )
    op.create_check_constraint(
        'ck_courses_status_valid',
        'courses',
        f"status IN {sql_value_list(CourseStatus)}"
    )

    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            # Every existing value was written by datetime.utcnow(), so it
            # is already UTC — this labels it rather than shifting it.
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )

    op.drop_constraint('ck_courses_status_valid', 'courses', type_='check')
    op.drop_constraint('ck_users_role_valid', 'users', type_='check')
