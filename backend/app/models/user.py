from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.constants import Department
from app.constants import Role
from app.constants import Seniority
from app.constants import sql_value_list

from app.database import Base


class User(Base):
    __tablename__ = "users"

    # Every value list here is rendered from the enum in app/constants.py,
    # so the database and the Python code cannot disagree about what a
    # valid department, seniority or role is.
    __table_args__ = (
        CheckConstraint(
            f"department IN {sql_value_list(Department)} "
            "OR department IS NULL",
            name="ck_users_department_valid"
        ),
        CheckConstraint(
            f"seniority IN {sql_value_list(Seniority)} "
            "OR seniority IS NULL",
            name="ck_users_seniority_valid"
        ),
        CheckConstraint(
            f"role IN {sql_value_list(Role)}",
            name="ck_users_role_valid"
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

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(200),
        unique=True,
        nullable=True,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    # Stamped into every access token this account is issued, and checked
    # on every request. Bumping it makes all existing tokens stop working
    # immediately.
    #
    # Without it, changing the password of a compromised account did not
    # lock the intruder out: their token stayed valid until it expired on
    # its own, which is up to ACCESS_TOKEN_EXPIRE_MINUTES later — eight
    # hours in the deployed configuration.
    token_version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default="1"
    )

    role = Column(
        String(50),
        nullable=False,
        default=Role.STUDENT.value
    )

    department = Column(
        String(100),
        nullable=True
    )

    seniority = Column(
        String(50),
        nullable=True
    )

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN.value
