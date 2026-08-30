from sqlalchemy.orm import Session

from app.constants import CourseStatus
from app.constants import Role

from app.errors import ConflictError
from app.errors import NotFoundError

from app.models.user import User
from app.models.course import Course
from app.models.certificate import Certificate
from app.models.progress import Progress
from app.models.quiz import QuizAttempt

from app.utils.security import hash_password


def get_dashboard(
    db: Session
):
    total_students = (
        db.query(User)
        .filter(User.role == Role.STUDENT.value)
        .count()
    )

    published_courses = (
        db.query(Course)
        .filter(Course.status == CourseStatus.PUBLISHED.value)
        .count()
    )

    draft_courses = (
        db.query(Course)
        .filter(Course.status == CourseStatus.DRAFT.value)
        .count()
    )

    return {
        "total_students": total_students,
        "published_courses": published_courses,
        "draft_courses": draft_courses
    }


def list_all_users(
    db: Session
):
    return (
        db.query(User)
        .order_by(User.name)
        .all()
    )


def create_user(
    db: Session,
    name: str,
    username: str,
    email: str,
    password: str,
    role: str,
    department: str | None,
    seniority: str | None
):
    if email and db.query(User).filter(User.email == email).first():
        raise ConflictError("Email already registered")

    if db.query(User).filter(User.username == username).first():
        raise ConflictError("Username already taken")

    user = User(
        name=name,
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        department=department,
        seniority=seniority
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(
    db: Session,
    user_id: int,
    name: str | None,
    username: str | None,
    email: str | None,
    password: str | None,
    role: str | None,
    department: str | None,
    seniority: str | None,
    provided_fields: set[str]
):
    user = db.get(User, user_id)

    if user is None:
        raise NotFoundError("User not found")

    if username is not None and username != user.username:
        if db.query(User).filter(User.username == username).first():
            raise ConflictError("Username already taken")
        user.username = username

    if "email" in provided_fields and email != user.email:
        if email and db.query(User).filter(User.email == email).first():
            raise ConflictError("Email already registered")
        user.email = email

    if name is not None:
        user.name = name

    if password:
        user.password_hash = hash_password(password)

    if role is not None:
        user.role = role

    if "department" in provided_fields:
        user.department = department

    if "seniority" in provided_fields:
        user.seniority = seniority

    db.commit()
    db.refresh(user)

    return user


def delete_user(
    db: Session,
    user_id: int
) -> dict[str, int]:
    """Delete an account and everything recorded against it.

    Their progress, quiz attempts and certificates go too, by database
    cascade. That is destructive and cannot be undone — a certificate is
    a record of something the person actually achieved — so the counts are
    returned and shown to the admin who asked for the deletion.

    Before the cascades existed, this could not delete anyone who had ever
    taken a quiz at all: the foreign keys refused, and the admin got a
    vague "may still have related records" message with no way forward.
    """
    user = db.get(User, user_id)

    if user is None:
        raise NotFoundError("User not found")

    removed = {
        "progress": (
            db.query(Progress)
            .filter(Progress.user_id == user_id)
            .count()
        ),
        "quiz_attempts": (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id)
            .count()
        ),
        "certificates": (
            db.query(Certificate)
            .filter(Certificate.user_id == user_id)
            .count()
        ),
    }

    db.delete(user)
    db.commit()

    return removed
