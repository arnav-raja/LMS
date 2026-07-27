from sqlalchemy.orm import Session

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
        return None

    course.status = "published"

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
        return None

    course.status = "archived"

    db.commit()
    db.refresh(course)

    return course
