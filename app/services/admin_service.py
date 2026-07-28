from sqlalchemy.orm import Session

from app.models.user import User
from app.models.course import Course
from app.models.course_access_rule import CourseAccessRule
from app.models.progress import Progress

from app.utils.security import hash_password


def get_dashboard(
    db: Session
):
    return {
        "students": (
            db.query(User)
            .filter(User.role == "student")
            .count()
        ),
        "courses": db.query(Course).count(),
        "access_rules": db.query(CourseAccessRule).count(),
        "completed_subchapters": (
            db.query(Progress)
            .filter(
                Progress.is_completed == True
            )
            .count()
        )
    }


def create_student(
    db: Session,
    name: str,
    email: str,
    password: str,
    department: str | None = None,
    seniority: str | None = None
):
    """Admins add students directly — there is no public sign-up."""
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise ValueError(
            "Email already registered"
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="student",
        department=department,
        seniority=seniority
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def delete_student(
    db: Session,
    user_id: int
) -> bool:
    user = db.get(User, user_id)

    if user is None or user.role != "student":
        return False

    # The users -> progress foreign key has no ON DELETE CASCADE, so their
    # completion history has to be cleared before the user row itself.
    (
        db.query(Progress)
        .filter(Progress.user_id == user_id)
        .delete()
    )

    db.delete(user)
    db.commit()

    return True


def update_student_profile(
    db: Session,
    user_id: int,
    department: str,
    seniority: str
):
    user = db.get(User, user_id)

    if user is None:
        return None

    user.department = department
    user.seniority = seniority

    db.commit()
    db.refresh(user)

    return user
