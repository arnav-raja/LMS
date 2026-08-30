from sqlalchemy.orm import Session

from app.constants import CourseStatus

from app.errors import NotFoundError

from app.models.course import Course


def get_course(
    db: Session,
    course_id: int
):
    return db.get(Course, course_id)


def get_courses(
    db: Session
):
    return (
        db.query(Course)
        .all()
    )


def publish_course(
    db: Session,
    course_id: int
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id
        )
        .first()
    )

    if course is None:
        raise NotFoundError("Course not found")

    course.status = CourseStatus.PUBLISHED.value

    db.commit()
    db.refresh(course)

    return course


def archive_course(
    db: Session,
    course_id: int
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id
        )
        .first()
    )

    if course is None:
        raise NotFoundError("Course not found")

    course.status = CourseStatus.ARCHIVED.value

    db.commit()
    db.refresh(course)

    return course
