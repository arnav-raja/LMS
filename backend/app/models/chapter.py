from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import relationship

from app.database import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    chapter_number = Column(
        Integer,
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    num_subchapters = Column(
        Integer,
        nullable=False,
        default=0
    )

    course = relationship(
        "Course",
        back_populates="chapters"
    )

    subchapters = relationship(
        "Subchapter",
        back_populates="chapter",
        cascade="all, delete-orphan"
    )

    quiz = relationship(
        "Quiz",
        back_populates="chapter",
        uselist=False,
        cascade="all, delete-orphan"
    )