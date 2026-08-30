from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import relationship

from app.constants import CourseStatus
from app.constants import sql_value_list

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    __table_args__ = (
        CheckConstraint(
            f"status IN {sql_value_list(CourseStatus)}",
            name="ck_courses_status_valid"
        ),
    )

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
        default=CourseStatus.DRAFT.value
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