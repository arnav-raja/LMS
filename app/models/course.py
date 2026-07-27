from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=False
    )

    num_chapters = Column(
        Integer,
        nullable=False,
        default=0
    )

    status = Column(
        String,
        nullable=False,
        default="draft"
    )

    chapters = relationship(
        "Chapter",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    access_rules = relationship(
        "CourseAccessRule",
        back_populates="course",
        cascade="all, delete-orphan"
    )