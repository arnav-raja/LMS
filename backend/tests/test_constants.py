"""The enums are the single source of truth for these values, and the
database CHECK constraints are rendered from them. If a value is added to
an enum without a migration, the two drift apart silently — these tests
make that visible."""

import pytest

from sqlalchemy.exc import IntegrityError

from app.constants import CourseStatus
from app.constants import Department
from app.constants import Role
from app.constants import Seniority
from app.constants import sql_value_list

from app.models.course import Course
from app.models.user import User
from app.utils.security import hash_password


def test_sql_value_list_renders_a_sql_in_list():
    assert sql_value_list(Role) == "('admin', 'student')"


def test_sql_value_list_covers_every_member():
    rendered = sql_value_list(Department)

    for member in Department:
        assert f"'{member.value}'" in rendered


@pytest.mark.parametrize(
    "enum_class, expected",
    [
        (Role, {"admin", "student"}),
        (CourseStatus, {"draft", "published", "archived"}),
        (Seniority, {"Manager", "Senior", "Mid", "Junior"}),
    ],
)
def test_enum_values_are_what_the_database_holds(enum_class, expected):
    """These strings are written into rows. Renaming one is a data
    migration, not a refactor — this test is here to make that obvious."""
    assert {member.value for member in enum_class} == expected


def test_database_rejects_a_role_outside_the_enum(db_session):
    db_session.add(
        User(
            name="Wizard",
            username="wizard",
            password_hash=hash_password("x"),
            role="wizard",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_rejects_a_status_outside_the_enum(db_session):
    db_session.add(
        Course(title="T", description="D", num_chapters=0, status="pending")
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_rejects_a_department_outside_the_enum(db_session):
    db_session.add(
        User(
            name="Nowhere",
            username="nowhere",
            password_hash=hash_password("x"),
            role=Role.STUDENT.value,
            department="ZZ",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_database_accepts_every_declared_department(db_session):
    for index, department in enumerate(Department):
        db_session.add(
            User(
                name=f"User {index}",
                username=f"user{index}",
                password_hash=hash_password("x"),
                role=Role.STUDENT.value,
                department=department.value,
                seniority=Seniority.MID.value,
            )
        )

    db_session.flush()
