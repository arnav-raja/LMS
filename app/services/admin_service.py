from sqlalchemy.orm import Session

from app.models.user import User
from app.models.course import Course
from app.models.progress import Progress

from app.utils.security import hash_password


def get_dashboard(
    db: Session
):
    total_students = (
        db.query(User)
        .filter(User.role == "student")
        .count()
    )

    published_courses = (
        db.query(Course)
        .filter(Course.status == "published")
        .count()
    )

    draft_courses = (
        db.query(Course)
        .filter(Course.status == "draft")
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
        raise ValueError("Email already registered")

    if db.query(User).filter(User.username == username).first():
        raise ValueError("Username already taken")

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
        return None

    if username is not None and username != user.username:
        if db.query(User).filter(User.username == username).first():
            raise ValueError("Username already taken")
        user.username = username

    if "email" in provided_fields and email != user.email:
        if email and db.query(User).filter(User.email == email).first():
            raise ValueError("Email already registered")
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
):
    user = db.get(User, user_id)

    if user is None:
        return False

    # Remove their progress history first — the database won't let us
    # delete the account itself while rows still point at it.
    db.query(Progress).filter(Progress.user_id == user_id).delete()

    db.delete(user)
    db.commit()

    return True
