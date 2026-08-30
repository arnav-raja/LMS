import pytest

from app.errors import NotFoundError
from app.models.course import Course
from app.models.user import User
from app.services import access_service
from app.utils.security import hash_password


def make_course(db_session, status="published", **overrides):
    defaults = dict(title="Onboarding", description="Intro course", status=status)
    defaults.update(overrides)

    course = Course(**defaults)
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    return course


def make_user(db_session, role="student", department="EC", seniority="Mid"):
    user = User(
        name="Grace Hopper",
        username="grace",
        email="grace@example.com",
        password_hash=hash_password("x"),
        role=role,
        department=department,
        seniority=seniority,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_admin_has_access_without_any_rule(db_session):
    course = make_course(db_session)
    admin = make_user(db_session, role="admin", department=None, seniority=None)

    assert access_service.user_has_access(db_session, admin, course.id) is True


def test_student_without_matching_rule_is_denied(db_session):
    course = make_course(db_session)
    student = make_user(db_session)

    assert access_service.user_has_access(db_session, student, course.id) is False


def test_student_with_granted_rule_is_allowed(db_session):
    course = make_course(db_session)
    student = make_user(db_session, department="EC", seniority="Mid")

    access_service.grant_access(db_session, course.id, "EC", "Mid")

    assert access_service.user_has_access(db_session, student, course.id) is True


def test_revoke_access_removes_permission(db_session):
    course = make_course(db_session)
    student = make_user(db_session, department="EC", seniority="Mid")
    access_service.grant_access(db_session, course.id, "EC", "Mid")

    access_service.revoke_access(db_session, course.id, "EC", "Mid")

    assert access_service.user_has_access(db_session, student, course.id) is False


def test_revoke_access_missing_rule_raises_not_found(db_session):
    course = make_course(db_session)

    with pytest.raises(NotFoundError):
        access_service.revoke_access(db_session, course.id, "EC", "Mid")


def test_accessible_courses_excludes_unpublished_for_students(db_session):
    published = make_course(db_session, status="published", title="Published")
    draft = make_course(db_session, status="draft", title="Draft")
    student = make_user(db_session, department="EC", seniority="Mid")

    access_service.grant_access(db_session, published.id, "EC", "Mid")
    access_service.grant_access(db_session, draft.id, "EC", "Mid")

    accessible = access_service.get_accessible_courses(db_session, student)

    assert [course.id for course in accessible] == [published.id]


def test_accessible_courses_returns_everything_for_admin(db_session):
    make_course(db_session, status="draft")
    make_course(db_session, status="published")
    admin = make_user(db_session, role="admin", department=None, seniority=None)

    accessible = access_service.get_accessible_courses(db_session, admin)

    assert len(accessible) == 2
