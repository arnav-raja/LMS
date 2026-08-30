from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.subchapter import Subchapter
from app.models.user import User

from app.services.access_service import get_accessible_courses
from app.services.progress_service import get_completed_subchapter_ids


def get_dashboard(
    db: Session,
    user: User
):
    """The student's own landing page: every course they can reach, how
    far through it they are, and what to open next.

    Loads every lesson of every accessible course in one query. It used to
    walk `course.chapters` and then `chapter.subchapters` as lazy
    relationships, which cost a query per course plus one per chapter —
    on the page every student sees first, every time they sign in.

    The ordering matters as much as the count. Those relationships have no
    `order_by`, so "next lesson" was whichever row the database happened
    to return first; it only looked right because rows usually come back
    in insertion order, and would have started lying the first time a
    course was edited.
    """
    accessible_courses = get_accessible_courses(db, user)
    course_ids = [course.id for course in accessible_courses]

    completed_subchapter_ids = get_completed_subchapter_ids(db, user.id)

    lessons_by_course: dict[int, list] = {
        course_id: [] for course_id in course_ids
    }

    if course_ids:
        rows = (
            db.query(
                Chapter.course_id,
                Subchapter.id,
                Subchapter.title,
            )
            .join(Chapter, Chapter.id == Subchapter.chapter_id)
            .filter(Chapter.course_id.in_(course_ids))
            .order_by(
                Chapter.course_id,
                Chapter.chapter_number,
                Subchapter.subchapter_number,
            )
            .all()
        )

        for row in rows:
            lessons_by_course[row.course_id].append(row)

    courses = []

    for course in accessible_courses:
        lessons = lessons_by_course[course.id]

        total_subchapters = len(lessons)
        completed_subchapters = 0
        next_subchapter = None

        for lesson in lessons:
            if lesson.id in completed_subchapter_ids:
                completed_subchapters += 1
            elif next_subchapter is None:
                next_subchapter = lesson.title

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
