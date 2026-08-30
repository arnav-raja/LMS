from sqlalchemy.orm import Session

from app.errors import NotFoundError

from app.models.course import Course
from app.models.chapter import Chapter
from app.models.subchapter import Subchapter
from app.models.progress import Progress

from app.schemas.course_builder import CreateCourseRequest


def _create_chapter(db: Session, course_id: int, chapter_number: int, chapter_data):
    """Create one chapter and its ordered subchapters."""
    chapter = Chapter(
        course_id=course_id,
        chapter_number=chapter_number,
        title=chapter_data.title,
        description=chapter_data.description,
        num_subchapters=len(chapter_data.subchapters)
    )
    db.add(chapter)
    db.flush()

    for subchapter_number, subchapter_data in enumerate(
        chapter_data.subchapters,
        start=1
    ):
        db.add(
            Subchapter(
                chapter_id=chapter.id,
                subchapter_number=subchapter_number,
                title=subchapter_data.title,
                content=subchapter_data.content
            )
        )

    return chapter


def create_course(
    db: Session,
    request: CreateCourseRequest
):
    course = Course(
        title=request.title,
        description=request.description,
        status=request.status.value,
        num_chapters=len(request.chapters)
    )

    db.add(course)
    db.flush()

    for chapter_index, chapter_data in enumerate(
        request.chapters,
        start=1
    ):
        _create_chapter(db, course.id, chapter_index, chapter_data)

    db.commit()
    db.refresh(course)

    return course


def _delete_progress_for_subchapters(
    db: Session,
    subchapter_ids: list[int]
):
    if not subchapter_ids:
        return

    (
        db.query(Progress)
        .filter(Progress.subchapter_id.in_(subchapter_ids))
        .delete(synchronize_session=False)
    )


def _sync_subchapters(
    db: Session,
    chapter: Chapter,
    subchapters_data
):
    """Update subchapters of an existing chapter in place, matched by
    position (subchapter_number), so subchapters that still exist keep
    their id and any progress recorded against them stays valid. Only
    subchapters that no longer exist in the request are removed - and
    their progress is explicitly cleared first, since nothing else
    could safely reference them afterwards."""
    existing_by_number = {
        subchapter.subchapter_number: subchapter
        for subchapter in (
            db.query(Subchapter)
            .filter(Subchapter.chapter_id == chapter.id)
            .all()
        )
    }

    new_numbers = set(range(1, len(subchapters_data) + 1))
    obsolete_numbers = set(existing_by_number) - new_numbers

    if obsolete_numbers:
        obsolete_ids = [
            existing_by_number[number].id
            for number in obsolete_numbers
        ]

        _delete_progress_for_subchapters(db, obsolete_ids)

        (
            db.query(Subchapter)
            .filter(Subchapter.id.in_(obsolete_ids))
            .delete(synchronize_session=False)
        )

    for subchapter_index, subchapter_data in enumerate(
        subchapters_data,
        start=1
    ):
        subchapter = existing_by_number.get(subchapter_index)

        if subchapter is None:
            db.add(
                Subchapter(
                    chapter_id=chapter.id,
                    subchapter_number=subchapter_index,
                    title=subchapter_data.title,
                    content=subchapter_data.content
                )
            )
        else:
            subchapter.title = subchapter_data.title
            subchapter.content = subchapter_data.content

    chapter.num_subchapters = len(subchapters_data)


def _delete_chapter_with_progress(
    db: Session,
    chapter: Chapter
):
    subchapter_ids = [
        row.id
        for row in (
            db.query(Subchapter.id)
            .filter(Subchapter.chapter_id == chapter.id)
            .all()
        )
    ]

    _delete_progress_for_subchapters(db, subchapter_ids)

    (
        db.query(Subchapter)
        .filter(Subchapter.chapter_id == chapter.id)
        .delete(synchronize_session=False)
    )

    db.delete(chapter)


def update_course(
    db: Session,
    course_id: int,
    request: CreateCourseRequest
):
    """Updates a course's content in place wherever possible. Chapters and
    subchapters are matched to the incoming request by position (chapter_
    number / subchapter_number); anything that still exists at the same
    position keeps its original id, so student progress recorded against
    it remains valid after the edit. Anything genuinely removed has its
    progress explicitly cleared before the row itself is deleted."""
    course = db.get(
        Course,
        course_id
    )

    if course is None:
        raise NotFoundError("Course not found")

    course.title = request.title
    course.description = request.description
    course.status = request.status.value
    course.num_chapters = len(request.chapters)

    existing_chapters_by_number = {
        chapter.chapter_number: chapter
        for chapter in (
            db.query(Chapter)
            .filter(Chapter.course_id == course.id)
            .all()
        )
    }

    new_chapter_numbers = set(range(1, len(request.chapters) + 1))
    obsolete_chapter_numbers = (
        set(existing_chapters_by_number) - new_chapter_numbers
    )

    for chapter_number in obsolete_chapter_numbers:
        _delete_chapter_with_progress(
            db,
            existing_chapters_by_number[chapter_number]
        )

    for chapter_index, chapter_data in enumerate(
        request.chapters,
        start=1
    ):
        chapter = existing_chapters_by_number.get(chapter_index)

        if chapter is None:
            _create_chapter(db, course.id, chapter_index, chapter_data)
            continue
        else:
            chapter.title = chapter_data.title
            chapter.description = chapter_data.description

        _sync_subchapters(
            db,
            chapter,
            chapter_data.subchapters
        )

    db.commit()
    db.refresh(course)

    return course


def delete_course(
    db: Session,
    course_id: int
):
    """Deleting a course is a deliberate, full removal: its chapters,
    subchapters, access rules, and any progress students had recorded
    against it are all removed too. (Editing a course, above, is the
    operation that preserves progress - deleting it outright does not.)"""
    course = db.get(
        Course,
        course_id
    )

    if course is None:
        raise NotFoundError("Course not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course.id)
        .all()
    )

    for chapter in chapters:
        _delete_chapter_with_progress(db, chapter)

    db.delete(course)

    db.commit()
