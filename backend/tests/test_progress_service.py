from app.models.chapter import Chapter
from app.models.course import Course
from app.models.subchapter import Subchapter
from app.models.user import User
from app.services import progress_service
from app.utils.security import hash_password


def make_subchapter(db_session):
    course = Course(title="Onboarding", description="Intro", status="published")
    db_session.add(course)
    db_session.commit()

    chapter = Chapter(course_id=course.id, chapter_number=1, title="Chapter 1")
    db_session.add(chapter)
    db_session.commit()

    subchapter = Subchapter(chapter_id=chapter.id, subchapter_number=1, title="Lesson 1")
    db_session.add(subchapter)
    db_session.commit()
    db_session.refresh(subchapter)

    return subchapter


def make_user(db_session):
    user = User(
        name="Alan Turing",
        username="alan",
        email="alan@example.com",
        password_hash=hash_password("x"),
        role="student",
        department="EC",
        seniority="Mid",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_complete_subchapter_creates_progress_row(db_session):
    subchapter = make_subchapter(db_session)
    user = make_user(db_session)

    progress = progress_service.complete_subchapter(db_session, user.id, subchapter.id)

    assert progress.is_completed is True
    assert progress.completed_at is not None
    assert subchapter.id in progress_service.get_completed_subchapter_ids(db_session, user.id)


def test_complete_subchapter_is_idempotent(db_session):
    subchapter = make_subchapter(db_session)
    user = make_user(db_session)

    progress_service.complete_subchapter(db_session, user.id, subchapter.id)
    progress_service.complete_subchapter(db_session, user.id, subchapter.id)

    rows = progress_service.get_user_progress(db_session, user.id)
    assert len(rows) == 1


def test_get_subchapter_course_id_resolves_through_chapter(db_session):
    subchapter = make_subchapter(db_session)
    course_id = subchapter.chapter.course_id

    resolved = progress_service.get_subchapter_course_id(db_session, subchapter.id)

    assert resolved == course_id


def test_get_subchapter_course_id_returns_none_for_unknown_subchapter(db_session):
    assert progress_service.get_subchapter_course_id(db_session, 9999) is None
