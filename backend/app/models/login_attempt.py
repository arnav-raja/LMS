from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base

from app.utils.time import utc_now


class LoginAttempt(Base):
    """One row per sign-in attempt, successful or not.

    Kept in the database rather than in process memory so the limit
    survives a restart and holds across more than one instance — an
    in-memory counter is reset by exactly the thing an attacker causes
    when they hammer a service, and is per-worker besides.

    Rows are pruned as they age out of the window, so this stays small.
    """

    __tablename__ = "login_attempts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # What was typed into the username field, which may be a username or
    # an email. Stored as given so the limit follows what the attacker is
    # trying, not the account they eventually find.
    #
    # Deliberately not a foreign key: attempts against accounts that do
    # not exist are the ones most worth counting.
    identifier = Column(
        String(200),
        nullable=False,
        index=True
    )

    succeeded = Column(
        Boolean,
        nullable=False,
        default=False
    )

    attempted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True
    )
