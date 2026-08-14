from app.models.chapter import Chapter
from app.models.course import Course
from app.models.quiz import Quiz
from app.models.quiz import QuizAttempt
from app.models.subchapter import Subchapter
from app.models.user import User
from app.services import chapter_service
from app.services import progress_service
from app.utils.security import hash_password


def make_course_with_two_chapters(db_session):
    course = Course(title="Onboarding", description="Intro", status="published")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    chapters = []
    for chapter_number in (1, 2):
        chapter = Chapter(course_id=course.id, chapter_number=chapter_number, title=f"Chapter {chapter_number}")
        db_session.add(chapter)
        db_session.commit()
        db_session.refresh(chapter)

        subchapter = Subchapter(chapter_id=chapter.id, subchapter_number=1, title="Lesson 1")
        db_session.add(subchapter)
        db_session.commit()
        db_session.refresh(subchapter)

        quiz = Quiz(chapter_id=chapter.id, title=f"Chapter {chapter_number} Quiz", passing_score=70)
        db_session.add(quiz)
        db_session.commit()
        db_session.refresh(quiz)

        chapters.append((chapter, subchapter, quiz))

    return course, chapters


def make_user(db_session, role="student"):
    user = User(
        name="Radia Perlman",
        username="radia",
        email="radia@example.com",
        password_hash=hash_password("x"),
        role=role,
        department="EC",
        seniority="Mid",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_course_chapters_for_user_reflects_quiz_pass_state_per_chapter(db_session):
    course, [(chapter1, subchapter1, quiz1), (chapter2, subchapter2, quiz2)] = (
        make_course_with_two_chapters(db_session)
    )
    user = make_user(db_session)

    progress_service.complete_subchapter(db_session, user.id, subchapter1.id)
    db_session.add(QuizAttempt(user_id=user.id, quiz_id=quiz1.id, score=100, passed=True))
    db_session.commit()

    result = chapter_service.get_course_chapters_for_user(db_session, course.id, user)

    first, second = result

    assert first["quiz"]["is_unlocked"] is True
    assert first["quiz"]["is_passed"] is True

    # Chapter 2's own subchapter is untouched, so its quiz reads as locked
    # even though chapter 1's quiz has already been passed.
    assert second["quiz"]["is_unlocked"] is False
    assert second["quiz"]["is_passed"] is False
