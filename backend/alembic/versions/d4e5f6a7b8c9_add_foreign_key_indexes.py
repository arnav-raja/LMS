"""add indexes on foreign key columns

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# These columns are filtered or joined on in hot-path queries (course
# player load, quiz submission, certificate checks) but had no index
# beyond the implicit one on each table's primary key.
INDEXES = [
    ('ix_chapters_course_id', 'chapters', 'course_id'),
    ('ix_subchapters_chapter_id', 'subchapters', 'chapter_id'),
    ('ix_progress_user_id', 'progress', 'user_id'),
    ('ix_progress_subchapter_id', 'progress', 'subchapter_id'),
    ('ix_quiz_questions_quiz_id', 'quiz_questions', 'quiz_id'),
    ('ix_quiz_options_question_id', 'quiz_options', 'question_id'),
    ('ix_quiz_attempts_user_id', 'quiz_attempts', 'user_id'),
    ('ix_quiz_attempts_quiz_id', 'quiz_attempts', 'quiz_id'),
    ('ix_quiz_answers_attempt_id', 'quiz_answers', 'attempt_id'),
    ('ix_quiz_answers_question_id', 'quiz_answers', 'question_id'),
    ('ix_certificates_user_id', 'certificates', 'user_id'),
    ('ix_certificates_course_id', 'certificates', 'course_id'),
]


def upgrade() -> None:
    """Upgrade schema."""
    for index_name, table_name, column_name in INDEXES:
        op.create_index(index_name, table_name, [column_name], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    for index_name, table_name, column_name in reversed(INDEXES):
        op.drop_index(index_name, table_name=table_name)
