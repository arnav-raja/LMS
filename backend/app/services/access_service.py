from sqlalchemy.orm import Session

from app.constants import CourseStatus

from app.errors import NotFoundError

from app.models.course import Course
from app.models.course_access_rule import CourseAccessRule
from app.models.user import User


def grant_access(
    db: Session,
    course_id: int,
    department: str,
    seniority: str
):
    existing = (
        db.query(CourseAccessRule)
        .filter(
            CourseAccessRule.course_id == course_id,
            CourseAccessRule.department == department,
            CourseAccessRule.seniority == seniority
        )
        .first()
    )

    if existing:
        return existing

    rule = CourseAccessRule(
        course_id=course_id,
        department=department,
        seniority=seniority
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return rule


def revoke_access(
    db: Session,
    course_id: int,
    department: str,
    seniority: str
) -> None:
    rule = (
        db.query(CourseAccessRule)
        .filter(
            CourseAccessRule.course_id == course_id,
            CourseAccessRule.department == department,
            CourseAccessRule.seniority == seniority
        )
        .first()
    )

    if rule is None:
        raise NotFoundError("Access rule not found")

    db.delete(rule)
    db.commit()


def get_course_access_rules(
    db: Session,
    course_id: int
):
    return (
        db.query(CourseAccessRule)
        .filter(CourseAccessRule.course_id == course_id)
        .all()
    )


def user_has_access(
    db: Session,
    user: User,
    course_id: int
) -> bool:
    if user.is_admin:
        return True

    if not user.department or not user.seniority:
        return False

    rule = (
        db.query(CourseAccessRule)
        .filter(
            CourseAccessRule.course_id == course_id,
            CourseAccessRule.department == user.department,
            CourseAccessRule.seniority == user.seniority
        )
        .first()
    )

    return rule is not None


def get_accessible_courses(
    db: Session,
    user: User
):
    if user.is_admin:
        return db.query(Course).all()

    if not user.department or not user.seniority:
        return []

    return (
        db.query(Course)
        .join(CourseAccessRule, CourseAccessRule.course_id == Course.id)
        .filter(
            Course.status == CourseStatus.PUBLISHED.value,
            CourseAccessRule.department == user.department,
            CourseAccessRule.seniority == user.seniority
        )
        .distinct()
        .all()
    )
