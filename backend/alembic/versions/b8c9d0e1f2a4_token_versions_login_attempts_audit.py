"""token versions, login attempt tracking, and the audit log

Revision ID: b8c9d0e1f2a4
Revises: a7b8c9d0e1f3
Create Date: 2026-08-30 14:00:00.000000

users.token_version
    Stamped into every access token and checked on every request.
    Bumping it makes existing tokens stop working immediately. Without it,
    resetting the password of a compromised account did not lock the
    intruder out — their token stayed valid until it expired on its own,
    up to eight hours later in the deployed configuration.

    NOTE: tokens issued before this deploy carry no version claim and are
    rejected, so everyone signs in once more after it lands.

login_attempts
    Sign-in is rate limited per identifier. Held in the database rather
    than process memory so the limit survives a restart and holds across
    instances. Rows are pruned as they age out of the window.

audit_entries
    Administrators can create accounts, reset anyone's password, change
    anyone's role, and delete an account together with its certificates.
    None of that left any trace at all.

    actor_id is SET NULL rather than CASCADE on purpose: what an admin did
    has to outlive their own account, or removing an admin would erase
    their trail.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a4'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'token_version',
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=200), nullable=False),
        sa.Column('succeeded', sa.Boolean(), nullable=False),
        sa.Column(
            'attempted_at',
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_login_attempts_id'), 'login_attempts', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_login_attempts_identifier'),
        'login_attempts',
        ['identifier'],
        unique=False,
    )
    op.create_index(
        op.f('ix_login_attempts_attempted_at'),
        'login_attempts',
        ['attempted_at'],
        unique=False,
    )

    op.create_table(
        'audit_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_name', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('summary', sa.String(length=500), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['actor_id'], ['users.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_audit_entries_id'), 'audit_entries', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_audit_entries_actor_id'),
        'audit_entries',
        ['actor_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_entries_action'),
        'audit_entries',
        ['action'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_entries_created_at'),
        'audit_entries',
        ['created_at'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_audit_entries_created_at'), table_name='audit_entries')
    op.drop_index(op.f('ix_audit_entries_action'), table_name='audit_entries')
    op.drop_index(op.f('ix_audit_entries_actor_id'), table_name='audit_entries')
    op.drop_index(op.f('ix_audit_entries_id'), table_name='audit_entries')
    op.drop_table('audit_entries')

    op.drop_index(
        op.f('ix_login_attempts_attempted_at'), table_name='login_attempts'
    )
    op.drop_index(
        op.f('ix_login_attempts_identifier'), table_name='login_attempts'
    )
    op.drop_index(op.f('ix_login_attempts_id'), table_name='login_attempts')
    op.drop_table('login_attempts')

    op.drop_column('users', 'token_version')
