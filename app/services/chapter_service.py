from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.user import User

from app.services.sequence_service import get_subchapter_lock_map
from app.services.quiz_service import get_quiz_summary_for_chapter


def get_course_chapters(
    db: Session,
    course_id: int
):
    return (
        db.query(Chapter)
        .filter(Chapter.course_id == course_id)
        .order_by(Chapter.chapter_number)
        .all()
    )


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
    db: Session,
    chapter: Chapter,
    lock_map: dict,
    bypass_lock: bool,
    user_id: int
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
        "quiz": get_quiz_summary_for_chapter(db, user_id, chapter.id)
    }


def get_course_chapters_for_user(
    db: Session,
    course_id: int,
    user: User
):
    chapters = get_course_chapters(db, course_id)
    lock_map = get_subchapter_lock_map(db, user.id, course_id)
    bypass_lock = user.is_admin

    return [
        serialize_chapter(db, chapter, lock_map, bypass_lock, user.id)
        for chapter in chapters
    ]


def get_chapter_for_user(
    db: Session,
    chapter: Chapter,
    user: User
):
    lock_map = get_subchapter_lock_map(db, user.id, chapter.course_id)
    bypass_lock = user.is_admin

    return serialize_chapter(db, chapter, lock_map, bypass_lock, user.id)
