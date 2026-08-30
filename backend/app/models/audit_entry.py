from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base

from app.utils.time import utc_now


class AuditEntry(Base):
    """A record of an administrative action.

    Admins here can create accounts, change anyone's password, change
    anyone's role, and delete an account along with its certificates.
    None of that left a trace: if a student's account vanished, there was
    nothing anywhere to say who did it or when.

    Deliberately append-only — nothing in the application updates or
    deletes a row here. It records what was asked for, not the data
    itself, so it never holds a password or a hash.
    """

    __tablename__ = "audit_entries"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # The admin who did it. Kept as SET NULL rather than CASCADE: when an
    # admin's own account is deleted, the record of what they did must
    # outlive it, or deleting yourself would erase your own trail.
    actor_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Copied at the time of the action, so the entry still reads properly
    # after the actor's account is gone or renamed.
    actor_name = Column(
        String(100),
        nullable=False
    )

    action = Column(
        String(50),
        nullable=False,
        index=True
    )

    # What was acted on. Not a foreign key — the row it points at is
    # frequently the one that was just deleted.
    target_type = Column(
        String(50),
        nullable=False
    )

    target_id = Column(
        Integer,
        nullable=True
    )

    # Enough to read the entry without looking anything else up, e.g.
    # "Deleted account 'ada' (2 certificates)".
    summary = Column(
        String(500),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True
    )
