from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.course import Course
from app.models.course_access_rule import CourseAccessRule
from app.models.progress import Progress

from app.services.access_service import get_accessible_courses
from app.utils.security import hash_password


def get_dashboard(
    db: Session
):
    students = (
        db.query(User)
        .filter(User.role == "student")
        .all()
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

    students_without_access = 0
    percentages = []

    for student in students:
        accessible_courses = get_accessible_courses(db, student)

        if len(accessible_courses) == 0:
            students_without_access += 1
            continue

        completed_subchapter_ids = {
            row.subchapter_id
            for row in (
                db.query(Progress.subchapter_id)
                .filter(
                    Progress.user_id == student.id,
                    Progress.is_completed == True
                )
                .all()
            )
        }

        total_subchapters = 0
        completed_subchapters = 0

        for course in accessible_courses:
            for chapter in course.chapters:
                for subchapter in chapter.subchapters:
                    total_subchapters += 1

                    if subchapter.id in completed_subchapter_ids:
                        completed_subchapters += 1

        if total_subchapters > 0:
            percentages.append(
                (completed_subchapters / total_subchapters) * 100
            )
        else:
            percentages.append(0)

    average_completion_percentage = (
        round(sum(percentages) / len(percentages), 2)
        if percentages
        else 0
    )

    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    completions_last_7_days = (
        db.query(Progress)
        .filter(
            Progress.is_completed == True,
            Progress.completed_at != None,
            Progress.completed_at >= seven_days_ago
        )
        .count()
    )

    return {
        "total_students": len(students),
        "published_courses": published_courses,
        "draft_courses": draft_courses,
        "students_without_access": students_without_access,
        "average_completion_percentage": average_completion_percentage,
        "completions_last_7_days": completions_last_7_days
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
    if db.query(User).filter(User.email == email).first():
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
    seniority: str | None
):
    user = db.get(User, user_id)

    if user is None:
        return None

    if username is not None and username != user.username:
        if db.query(User).filter(User.username == username).first():
            raise ValueError("Username already taken")
        user.username = username

    if email is not None and email != user.email:
        if db.query(User).filter(User.email == email).first():
            raise ValueError("Email already registered")
        user.email = email

    if name is not None:
        user.name = name

    if password:
        user.password_hash = hash_password(password)

    if role is not None:
        user.role = role

    if department is not None:
        user.department = department

    if seniority is not None:
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

    db.delete(user)
    db.commit()

    return True


def update_user_access_profile(
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
