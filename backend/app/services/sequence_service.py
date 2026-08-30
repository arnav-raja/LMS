from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.subchapter import Subchapter

from app.services.progress_service import get_completed_subchapter_ids
from app.services.quiz_service import get_quiz_gate_maps


def get_course_subchapter_sequences(
    db: Session,
    course_ids: list[int]
) -> dict[int, list[Subchapter]]:
    """{course_id: subchapters, in the order they must be completed} for
    any number of courses, in one query.

    The order is chapter 1's subchapters, then chapter 2's, and so on.
    """
    if not course_ids:
        return {}

    rows = (
        db.query(Subchapter, Chapter.course_id)
        .join(Chapter, Chapter.id == Subchapter.chapter_id)
        .filter(Chapter.course_id.in_(course_ids))
        .order_by(
            Chapter.course_id,
            Chapter.chapter_number,
            Subchapter.subchapter_number
        )
        .all()
    )

    sequences: dict[int, list[Subchapter]] = {
        course_id: [] for course_id in course_ids
    }

    for subchapter, course_id in rows:
        sequences[course_id].append(subchapter)

    return sequences


def get_course_subchapter_sequence(
    db: Session,
    course_id: int
):
    """The full, course-wide order subchapters must be completed in:
    chapter 1's subchapters in order, then chapter 2's, and so on."""
    return get_course_subchapter_sequences(db, [course_id]).get(course_id, [])


def _build_lock_map(
    sequence: list[Subchapter],
    completed_ids: set[int],
    quiz_gate_map: dict[int, dict]
) -> dict[int, dict]:
    """The unlock rule itself, with no database access.

    A subchapter unlocks only once the one immediately before it (in
    course order) has been completed; the first is always unlocked.

    Since each chapter's quiz is mandatory, the first subchapter of a new
    chapter also stays locked until the previous chapter's quiz has been
    passed. Chapters without a quiz never gate on this.
    """
    lock_map: dict[int, dict] = {}
    previous_completed = True
    previous_chapter_id = None

    for subchapter in sequence:
        is_completed = subchapter.id in completed_ids
        is_first_in_chapter = subchapter.chapter_id != previous_chapter_id

        if is_first_in_chapter and previous_chapter_id is not None:
            previous_chapter_gate = quiz_gate_map.get(
                previous_chapter_id,
                {"passed": True}
            )
            previous_completed = previous_completed and previous_chapter_gate["passed"]

        lock_map[subchapter.id] = {
            "is_completed": is_completed,
            "is_locked": not previous_completed
        }

        previous_completed = is_completed
        previous_chapter_id = subchapter.chapter_id

    return lock_map


def get_subchapter_lock_maps(
    db: Session,
    user_id: int,
    course_ids: list[int]
) -> dict[int, dict[int, dict]]:
    """{course_id: {subchapter_id: {is_completed, is_locked}}} for any
    number of courses, in a fixed number of queries.

    The admin's per-student progress page needs this for every course a
    student can reach. Calling the single-course version in a loop cost
    five or six queries per course, which is what made that page's cost
    grow with the size of the catalogue rather than with the student.
    """
    if not course_ids:
        return {}

    sequences = get_course_subchapter_sequences(db, course_ids)
    completed_ids = get_completed_subchapter_ids(db, user_id)
    gate_maps = get_quiz_gate_maps(db, user_id, course_ids)

    return {
        course_id: _build_lock_map(
            sequences.get(course_id, []),
            completed_ids,
            gate_maps.get(course_id, {}),
        )
        for course_id in course_ids
    }


def get_subchapter_lock_map(
    db: Session,
    user_id: int,
    course_id: int
) -> dict[int, dict]:
    """For every subchapter in one course, whether the user has completed
    it and whether it is locked."""
    return get_subchapter_lock_maps(db, user_id, [course_id]).get(course_id, {})


def is_subchapter_unlocked(
    db: Session,
    user_id: int,
    course_id: int,
    subchapter_id: int
) -> bool:
    lock_map = get_subchapter_lock_map(db, user_id, course_id)
    entry = lock_map.get(subchapter_id)

    return entry is not None and not entry["is_locked"]
