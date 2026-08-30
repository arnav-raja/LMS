from sqlalchemy.orm import Session

from app.errors import NotFoundError

from app.models.chapter import Chapter
from app.models.subchapter import Subchapter

from app.services.progress_service import get_completed_subchapter_ids


def continue_learning(
    db: Session,
    user_id: int,
    course_id: int
):
    chapters = (
        db.query(Chapter)
        .filter(
            Chapter.course_id == course_id
        )
        .order_by(
            Chapter.chapter_number
        )
        .all()
    )

    completed_subchapter_ids = get_completed_subchapter_ids(
        db,
        user_id
    )

    for chapter in chapters:

        subchapters = (
            db.query(Subchapter)
            .filter(
                Subchapter.chapter_id == chapter.id
            )
            .order_by(
                Subchapter.subchapter_number
            )
            .all()
        )

        for subchapter in subchapters:

            if subchapter.id not in completed_subchapter_ids:

                return {
                    "course_id": course_id,

                    "chapter_id": chapter.id,
                    "chapter_number": chapter.chapter_number,
                    "chapter_title": chapter.title,

                    "subchapter_id": subchapter.id,
                    "subchapter_number": subchapter.subchapter_number,
                    "subchapter_title": subchapter.title
                }

    # Nothing left unfinished. The frontend reads this 404 as "course
    # complete" and shows the finished state, not an error.
    raise NotFoundError("Course completed")


def get_course_progress(
    db: Session,
    user_id: int,
    course_id: int
):
    chapters = (
        db.query(Chapter)
        .filter(
            Chapter.course_id == course_id
        )
        .order_by(
            Chapter.chapter_number
        )
        .all()
    )

    completed_subchapter_ids = get_completed_subchapter_ids(
        db,
        user_id
    )

    total_chapters = len(chapters)

    total_subchapters = 0
    completed_subchapters = 0
    completed_chapters = 0

    for chapter in chapters:

        subchapters = (
            db.query(Subchapter)
            .filter(
                Subchapter.chapter_id == chapter.id
            )
            .order_by(
                Subchapter.subchapter_number
            )
            .all()
        )

        chapter_completed = len(subchapters) > 0

        for subchapter in subchapters:

            total_subchapters += 1

            if subchapter.id in completed_subchapter_ids:
                completed_subchapters += 1
            else:
                chapter_completed = False

        if chapter_completed:
            completed_chapters += 1

    percentage = 0

    if total_subchapters > 0:
        percentage = (
            completed_subchapters /
            total_subchapters
        ) * 100

    return {
        "course_id": course_id,

        "completed_subchapters": completed_subchapters,
        "total_subchapters": total_subchapters,

        "completed_chapters": completed_chapters,
        "total_chapters": total_chapters,

        "percentage": round(
            percentage,
            2
        )
    }
