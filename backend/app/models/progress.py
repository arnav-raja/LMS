
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer

from sqlalchemy.orm import relationship

from app.database import Base


class Progress(Base):
    __tablename__ = "progress"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    subchapter_id = Column(
        Integer,
        ForeignKey("subchapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    is_completed = Column(
        Boolean,
        nullable=False,
        default=False
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    user = relationship("User")

    subchapter = relationship("Subchapter")