from sqlalchemy.orm import Session

from app.models.user import User
from app.models.progress import Progress

from app.services.access_service import get_accessible_courses


def get_dashboard(
    db: Session,
    user: User
):
    accessible_courses = get_accessible_courses(db, user)

    completed_subchapter_ids = {
        row.subchapter_id
        for row in (
            db.query(Progress.subchapter_id)
            .filter(
                Progress.user_id == user.id,
                Progress.is_completed == True
            )
            .all()
        )
    }

    courses = []

    for course in accessible_courses:

        total_subchapters = 0
        completed_subchapters = 0
        next_subchapter = None

        for chapter in course.chapters:
            for subchapter in chapter.subchapters:
                total_subchapters += 1

                if subchapter.id in completed_subchapter_ids:
                    completed_subchapters += 1
                elif next_subchapter is None:
                    next_subchapter = subchapter.title

        progress_percentage = 0

        if total_subchapters > 0:
            progress_percentage = round(
                (completed_subchapters / total_subchapters) * 100,
                2
            )

        courses.append(
            {
                "id": course.id,
                "title": course.title,
                "progress": progress_percentage,
                "next_subchapter": next_subchapter
            }
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "courses": courses
    }
