from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.subchapter import Subchapter

from app.services.progress_service import get_completed_subchapter_ids


def get_course_subchapter_sequence(
    db: Session,
    course_id: int
):
    """The full, course-wide order subchapters must be completed in:
    chapter 1's subchapters in order, then chapter 2's, and so on."""
    return (
        db.query(Subchapter)
        .join(Chapter, Chapter.id == Subchapter.chapter_id)
        .filter(Chapter.course_id == course_id)
        .order_by(Chapter.chapter_number, Subchapter.subchapter_number)
        .all()
    )


def get_subchapter_lock_map(
    db: Session,
    user_id: int,
    course_id: int
) -> dict[int, dict]:
    """For every subchapter in the course, whether the user has completed
    it and whether it is locked. A subchapter unlocks only once the one
    immediately before it (in course order) has been completed; the
    first subchapter is always unlocked."""
    sequence = get_course_subchapter_sequence(db, course_id)
    completed_ids = get_completed_subchapter_ids(db, user_id)

    lock_map: dict[int, dict] = {}
    previous_completed = True

    for subchapter in sequence:
        is_completed = subchapter.id in completed_ids

        lock_map[subchapter.id] = {
            "is_completed": is_completed,
            "is_locked": not previous_completed
        }

        previous_completed = is_completed

    return lock_map


def is_subchapter_unlocked(
    db: Session,
    user_id: int,
    course_id: int,
    subchapter_id: int
) -> bool:
    lock_map = get_subchapter_lock_map(db, user_id, course_id)
    entry = lock_map.get(subchapter_id)

    return entry is not None and not entry["is_locked"]
