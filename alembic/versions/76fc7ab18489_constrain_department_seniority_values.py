"""constrain department/seniority to fixed value lists

Revision ID: 76fc7ab18489
Revises: 65fb383cc210
Create Date: 2026-07-25 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '76fc7ab18489'
down_revision: Union[str, Sequence[str], None] = '65fb383cc210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEPARTMENT_CODES = "('CR', 'DE', 'EC', 'FI', 'HR', 'IN', 'MK', 'OP', 'SA')"
SENIORITY_VALUES = "('Manager', 'Senior', 'Mid', 'Junior')"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        'ck_users_department_valid',
        'users',
        f"department IN {DEPARTMENT_CODES} OR department IS NULL"
    )
    op.create_check_constraint(
        'ck_users_seniority_valid',
        'users',
        f"seniority IN {SENIORITY_VALUES} OR seniority IS NULL"
    )
    op.create_check_constraint(
        'ck_course_access_rules_department_valid',
        'course_access_rules',
        f"department IN {DEPARTMENT_CODES}"
    )
    op.create_check_constraint(
        'ck_course_access_rules_seniority_valid',
        'course_access_rules',
        f"seniority IN {SENIORITY_VALUES}"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'ck_course_access_rules_seniority_valid',
        'course_access_rules',
        type_='check'
    )
    op.drop_constraint(
        'ck_course_access_rules_department_valid',
        'course_access_rules',
        type_='check'
    )
    op.drop_constraint('ck_users_seniority_valid', 'users', type_='check')
    op.drop_constraint('ck_users_department_valid', 'users', type_='check')
