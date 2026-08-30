from sqlalchemy.orm import Session

from app.errors import NotFoundError

from app.models.course import Course
from app.models.chapter import Chapter
from app.models.subchapter import Subchapter

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


def _validate_ids(request: CreateCourseRequest, existing_chapters: dict):
    """Check every id in the request before anything is modified.

    Ids come from the client, so two things have to be rejected: an id
    belonging to a different course (which would let one course's save
    reach into another's content) and an id that does not exist. Doing it
    up front rather than as we go is what makes a rejected save leave the
    course exactly as it was, instead of half applied.
    """
    for chapter_data in request.chapters:
        if chapter_data.id is None:
            # A chapter being created cannot already own subchapters.
            for subchapter_data in chapter_data.subchapters:
                if subchapter_data.id is not None:
                    raise NotFoundError(
                        f"Subchapter {subchapter_data.id} is not part of "
                        "this chapter"
                    )
            continue

        chapter = existing_chapters.get(chapter_data.id)

        if chapter is None:
            raise NotFoundError(
                f"Chapter {chapter_data.id} is not part of this course"
            )

        valid_subchapter_ids = {
            subchapter.id for subchapter in chapter.subchapters
        }

        for subchapter_data in chapter_data.subchapters:
            if (
                subchapter_data.id is not None
                and subchapter_data.id not in valid_subchapter_ids
            ):
                raise NotFoundError(
                    f"Subchapter {subchapter_data.id} is not part of "
                    "this chapter"
                )


def _sync_subchapters(
    db: Session,
    chapter: Chapter,
    subchapters_data
):
    """Bring one chapter's subchapters in line with the request.

    A subchapter carrying an id is the same lesson as before, wherever it
    now sits in the list — it keeps its id, so every Progress row pointing
    at it stays correct. One with no id is new. One that is no longer in
    the request is deleted, and the database cascades its progress away.
    """
    existing = {
        subchapter.id: subchapter
        for subchapter in (
            db.query(Subchapter)
            .filter(Subchapter.chapter_id == chapter.id)
            .all()
        )
    }

    kept_ids: set[int] = set()

    for position, subchapter_data in enumerate(subchapters_data, start=1):
        if subchapter_data.id is None:
            db.add(
                Subchapter(
                    chapter_id=chapter.id,
                    subchapter_number=position,
                    title=subchapter_data.title,
                    content=subchapter_data.content
                )
            )
            continue

        subchapter = existing.get(subchapter_data.id)

        if subchapter is None:
            # Either the id does not exist, or it belongs to a different
            # chapter. Refusing both keeps one course's edit from
            # reaching into another's content.
            raise NotFoundError(
                f"Subchapter {subchapter_data.id} is not part of this chapter"
            )

        subchapter.subchapter_number = position
        subchapter.title = subchapter_data.title
        subchapter.content = subchapter_data.content
        kept_ids.add(subchapter.id)

    for subchapter_id, subchapter in existing.items():
        if subchapter_id not in kept_ids:
            db.delete(subchapter)

    chapter.num_subchapters = len(subchapters_data)


def update_course(
    db: Session,
    course_id: int,
    request: CreateCourseRequest
):
    """Update a course's content in place.

    Chapters and subchapters are matched to the request by **id**. Anything
    that still carries its id keeps that id no matter where it has moved in
    the list, so student progress recorded against it survives the edit —
    including a reorder.

    This used to match by position instead, which meant swapping two
    chapters handed every student's completion history for one to the
    other, silently and with no way to notice.
    """
    course = db.get(
        Course,
        course_id
    )

    if course is None:
        raise NotFoundError("Course not found")

    existing_chapters = {
        chapter.id: chapter
        for chapter in (
            db.query(Chapter)
            .filter(Chapter.course_id == course.id)
            .all()
        )
    }

    _validate_ids(request, existing_chapters)

    course.title = request.title
    course.description = request.description
    course.status = request.status.value
    course.num_chapters = len(request.chapters)

    kept_ids: set[int] = set()

    for position, chapter_data in enumerate(request.chapters, start=1):
        if chapter_data.id is None:
            _create_chapter(db, course.id, position, chapter_data)
            continue

        chapter = existing_chapters.get(chapter_data.id)

        if chapter is None:
            raise NotFoundError(
                f"Chapter {chapter_data.id} is not part of this course"
            )

        chapter.chapter_number = position
        chapter.title = chapter_data.title
        chapter.description = chapter_data.description
        kept_ids.add(chapter.id)

        _sync_subchapters(db, chapter, chapter_data.subchapters)

    for chapter_id, chapter in existing_chapters.items():
        if chapter_id not in kept_ids:
            # Cascades take the subchapters, their progress, and the
            # chapter's quiz with it.
            db.delete(chapter)

    db.commit()
    db.refresh(course)

    return course


def delete_course(
    db: Session,
    course_id: int
):
    """Deleting a course is a deliberate, full removal: its chapters,
    subchapters, quizzes, access rules, and any progress students had
    recorded against it all go with it, by database cascade.

    (Editing a course, above, is the operation that preserves progress —
    deleting it outright does not.)"""
    course = db.get(
        Course,
        course_id
    )

    if course is None:
        raise NotFoundError("Course not found")

    db.delete(course)

    db.commit()
