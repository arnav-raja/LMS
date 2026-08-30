"""cascade deletes, and version quizzes instead of replacing them

Revision ID: a7b8c9d0e1f3
Revises: f6a7b8c9d0e1
Create Date: 2026-08-30 13:00:00.000000

Cascades
--------
Six foreign keys had no ON DELETE behaviour, so the application had to
clean up after itself and, where it forgot, the database simply refused
the delete. Deleting a student who had ever taken a quiz failed outright,
and the admin was told only that they "may still have related records".

The cleanup now belongs to the database:

    progress.user_id            -> CASCADE
    quiz_attempts.user_id       -> CASCADE
    certificates.user_id        -> CASCADE
    chapters.course_id          -> CASCADE
    subchapters.chapter_id      -> CASCADE
    course_access_rules.course_id -> CASCADE

Deleting an account now also deletes its certificates. That is a real
loss of a record of something someone earned, so the delete endpoint
reports what went with it.

Quiz versioning
---------------
Saving a quiz from the builder used to delete the quiz row and build a
new one, which cascaded away every attempt ever recorded against it — a
student who had passed simply no longer had. The quiz row now survives an
edit, and `version` counts the content changes so an attempt can still be
read against the questions it actually answered.

Existing rows all start at version 1, which is correct: whatever is
stored now is the first version anyone can have attempted.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f3'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (constraint name, table, referenced table, column)
CASCADES = [
    ("progress_user_id_fkey", "progress", "users", "user_id"),
    ("quiz_attempts_user_id_fkey", "quiz_attempts", "users", "user_id"),
    ("certificates_user_id_fkey", "certificates", "users", "user_id"),
    ("chapters_course_id_fkey", "chapters", "courses", "course_id"),
    ("subchapters_chapter_id_fkey", "subchapters", "chapters", "chapter_id"),
    (
        "course_access_rules_course_id_fkey",
        "course_access_rules",
        "courses",
        "course_id",
    ),
]


def upgrade() -> None:
    """Upgrade schema."""
    for name, table, referred_table, column in CASCADES:
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(
            name,
            table,
            referred_table,
            [column],
            ["id"],
            ondelete="CASCADE",
        )

    op.add_column(
        'quizzes',
        sa.Column(
            'version',
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        'quiz_attempts',
        sa.Column(
            'quiz_version',
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('quiz_attempts', 'quiz_version')
    op.drop_column('quizzes', 'version')

    for name, table, referred_table, column in CASCADES:
        op.drop_constraint(name, table, type_='foreignkey')
        op.create_foreign_key(
            name,
            table,
            referred_table,
            [column],
            ["id"],
        )
