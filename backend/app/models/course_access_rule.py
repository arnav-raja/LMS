from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import relationship

from app.database import Base


class CourseAccessRule(Base):
    __tablename__ = "course_access_rules"

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "department",
            "seniority",
            name="uq_course_department_seniority"
        ),
        CheckConstraint(
            "department IN ('CR', 'DE', 'EC', 'FI', 'HR', 'IN', 'MK', 'OP', 'SA')",
            name="ck_course_access_rules_department_valid"
        ),
        CheckConstraint(
            "seniority IN ('Manager', 'Senior', 'Mid', 'Junior')",
            name="ck_course_access_rules_seniority_valid"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    department = Column(
        String(100),
        nullable=False
    )

    seniority = Column(
        String(50),
        nullable=False
    )

    course = relationship(
        "Course",
        back_populates="access_rules"
    )
