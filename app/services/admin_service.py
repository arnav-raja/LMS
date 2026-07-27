from sqlalchemy.orm import Session

from app.models.user import User
from app.models.course import Course
from app.models.course_access_rule import CourseAccessRule
from app.models.progress import Progress


def get_dashboard(
    db: Session
):
    return {
        "users": db.query(User).count(),
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
