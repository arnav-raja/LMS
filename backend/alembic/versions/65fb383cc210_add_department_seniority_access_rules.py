"""add department/seniority to users and create course_access_rules

Revision ID: 65fb383cc210
Revises: 9d8d84b4fc80
Create Date: 2026-07-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65fb383cc210'
down_revision: Union[str, Sequence[str], None] = '9d8d84b4fc80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('department', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('seniority', sa.String(length=50), nullable=True)
    )

    op.create_table(
        'course_access_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('seniority', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'course_id', 'department', 'seniority',
            name='uq_course_department_seniority'
        )
    )
    op.create_index(
        op.f('ix_course_access_rules_id'),
        'course_access_rules',
        ['id'],
        unique=False
    )

    # Enrollment is replaced by department/seniority-based access rules.
    op.drop_table('enrollments')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_enrollments_id'), 'enrollments', ['id'], unique=False
    )

    op.drop_index(
        op.f('ix_course_access_rules_id'), table_name='course_access_rules'
    )
    op.drop_table('course_access_rules')

    op.drop_column('users', 'seniority')
    op.drop_column('users', 'department')
