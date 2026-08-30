from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.chapter import Chapter
from app.models.course import Course
from app.models.quiz import Quiz
from app.models.user import User

from app.services.sequence_service import get_subchapter_lock_map
from app.services.progress_service import get_completed_subchapter_ids
from app.services.quiz_service import get_quiz_summaries_for_course


def get_course_chapters(
    db: Session,
    course_id: int
):
    # selectinload, not a lazy relationship: every caller goes straight on
    # to read `chapter.subchapters`, which otherwise costs one query per
    # chapter in the course.
    return (
        db.query(Chapter)
        .options(selectinload(Chapter.subchapters))
        .filter(Chapter.course_id == course_id)
        .order_by(Chapter.chapter_number)
        .all()
    )


def list_all_chapters_admin(db: Session) -> list[dict]:
    """Every chapter in the system with its course, and whether it already
    has a quiz. One query.

    Exists because the admin Quizzes page needs a list of chapters to
    attach a quiz to. It was building that by calling the course player's
    endpoint once per course — one HTTP round trip each, every one of them
    computing lock maps and quiz summaries the page never looked at. Forty
    courses meant forty requests before the page could be used.
    """
    rows = (
        db.query(
            Chapter.id,
            Chapter.chapter_number,
            Chapter.title,
            Course.id.label("course_id"),
            Course.title.label("course_title"),
            Quiz.id.label("quiz_id"),
        )
        .join(Course, Course.id == Chapter.course_id)
        .outerjoin(Quiz, Quiz.chapter_id == Chapter.id)
        .order_by(Course.title, Chapter.chapter_number)
        .all()
    )

    return [
        {
            "id": row.id,
            "chapter_number": row.chapter_number,
            "title": row.title,
            "course_id": row.course_id,
            "course_title": row.course_title,
            "has_quiz": row.quiz_id is not None,
        }
        for row in rows
    ]


def get_chapter(
    db: Session,
    chapter_id: int
):
    return (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id)
        .first()
    )


def _serialize_subchapter(subchapter, lock_map, bypass_lock: bool) -> dict:
    entry = lock_map.get(
        subchapter.id,
        {"is_completed": False, "is_locked": True}
    )

    is_locked = entry["is_locked"] and not bypass_lock

    return {
        "id": subchapter.id,
        "chapter_id": subchapter.chapter_id,
        "subchapter_number": subchapter.subchapter_number,
        "title": subchapter.title,
        "content": None if is_locked else subchapter.content,
        "is_completed": entry["is_completed"],
        "is_locked": is_locked
    }


def serialize_chapter(
    chapter: Chapter,
    lock_map: dict,
    bypass_lock: bool,
    quiz_summary: dict | None
) -> dict:
    subchapters = sorted(
        chapter.subchapters,
        key=lambda subchapter: subchapter.subchapter_number
    )

    return {
        "id": chapter.id,
        "course_id": chapter.course_id,
        "chapter_number": chapter.chapter_number,
        "title": chapter.title,
        "description": chapter.description,
        "num_subchapters": chapter.num_subchapters,
        "subchapters": [
            _serialize_subchapter(subchapter, lock_map, bypass_lock)
            for subchapter in subchapters
        ],
        "quiz": quiz_summary
    }


def get_course_chapters_for_user(
    db: Session,
    course_id: int,
    user: User
):
    chapters = get_course_chapters(db, course_id)
    lock_map = get_subchapter_lock_map(db, user.id, course_id)
    bypass_lock = user.is_admin

    # Both of these are fetched once for the whole course. They used to be
    # resolved per chapter, which meant the player's cost grew with the
    # length of the course it was rendering.
    completed_subchapter_ids = get_completed_subchapter_ids(db, user.id)
    quiz_summaries = get_quiz_summaries_for_course(
        db, user.id, course_id, completed_subchapter_ids
    )

    return [
        serialize_chapter(
            chapter,
            lock_map,
            bypass_lock,
            quiz_summaries.get(chapter.id),
        )
        for chapter in chapters
    ]


def get_chapter_for_user(
    db: Session,
    chapter: Chapter,
    user: User
):
    lock_map = get_subchapter_lock_map(db, user.id, chapter.course_id)
    bypass_lock = user.is_admin
    quiz_summaries = get_quiz_summaries_for_course(
        db, user.id, chapter.course_id
    )

    return serialize_chapter(
        chapter,
        lock_map,
        bypass_lock,
        quiz_summaries.get(chapter.id),
    )
