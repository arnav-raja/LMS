import secrets

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import relationship

from app.database import Base

from app.utils.time import utc_now


def _generate_certificate_number() -> str:
    return f"ARNAV-{secrets.token_hex(8).upper()}"


class Certificate(Base):
    __tablename__ = "certificates"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "course_id",
            name="uq_certificate_user_course"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Publicly displayable proof-of-completion reference, independent of
    # the internal primary key.
    certificate_number = Column(
        String(40),
        nullable=False,
        unique=True,
        default=_generate_certificate_number
    )

    issued_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    user = relationship("User")

    course = relationship("Course")
