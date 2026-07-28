from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "department IN ('CR', 'DE', 'EC', 'FI', 'HR', 'IN', 'MK', 'OP', 'SA') "
            "OR department IS NULL",
            name="ck_users_department_valid"
        ),
        CheckConstraint(
            "seniority IN ('Manager', 'Senior', 'Mid', 'Junior') "
            "OR seniority IS NULL",
            name="ck_users_seniority_valid"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(200),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="student"
    )

    department = Column(
        String(100),
        nullable=True
    )

    seniority = Column(
        String(50),
        nullable=True
    )