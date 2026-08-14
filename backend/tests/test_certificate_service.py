from app.models.chapter import Chapter
from app.models.course import Course
from app.models.quiz import Quiz
from app.models.quiz import QuizAttempt
from app.models.subchapter import Subchapter
from app.models.user import User
from app.services import certificate_service
from app.services import progress_service
from app.utils.security import hash_password


def make_course_with_chapter(db_session, with_quiz=False):
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

    quiz = None
    if with_quiz:
        quiz = Quiz(chapter_id=chapter.id, title="Chapter 1 Quiz", passing_score=70)
        db_session.add(quiz)
        db_session.commit()
        db_session.refresh(quiz)

    return course, chapter, subchapter, quiz


def make_user(db_session):
    user = User(
        name="Katherine Johnson",
        username="katherine",
        email="katherine@example.com",
        password_hash=hash_password("x"),
        role="student",
        department="EC",
        seniority="Mid",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_course_without_quiz_is_complete_once_subchapters_done(db_session):
    course, _, subchapter, _ = make_course_with_chapter(db_session, with_quiz=False)
    user = make_user(db_session)

    progress_service.complete_subchapter(db_session, user.id, subchapter.id)

    assert certificate_service.is_course_complete(db_session, user.id, course.id) is True


def test_course_with_unpassed_quiz_is_not_complete(db_session):
    course, _, subchapter, quiz = make_course_with_chapter(db_session, with_quiz=True)
    user = make_user(db_session)

    progress_service.complete_subchapter(db_session, user.id, subchapter.id)

    assert certificate_service.is_course_complete(db_session, user.id, course.id) is False


def test_course_with_passed_quiz_is_complete(db_session):
    course, _, subchapter, quiz = make_course_with_chapter(db_session, with_quiz=True)
    user = make_user(db_session)

    progress_service.complete_subchapter(db_session, user.id, subchapter.id)
    db_session.add(QuizAttempt(user_id=user.id, quiz_id=quiz.id, score=90, passed=True))
    db_session.commit()

    assert certificate_service.is_course_complete(db_session, user.id, course.id) is True


def test_check_and_issue_certificate_issues_once_complete(db_session):
    course, _, subchapter, _ = make_course_with_chapter(db_session, with_quiz=False)
    user = make_user(db_session)
    progress_service.complete_subchapter(db_session, user.id, subchapter.id)

    certificate, newly_issued = certificate_service.check_and_issue_certificate(
        db_session, user.id, course.id
    )

    assert newly_issued is True
    assert certificate is not None
    assert certificate.certificate_number.startswith("ARNAV-")


def test_check_and_issue_certificate_is_not_reissued(db_session):
    course, _, subchapter, _ = make_course_with_chapter(db_session, with_quiz=False)
    user = make_user(db_session)
    progress_service.complete_subchapter(db_session, user.id, subchapter.id)

    first, first_new = certificate_service.check_and_issue_certificate(db_session, user.id, course.id)
    second, second_new = certificate_service.check_and_issue_certificate(db_session, user.id, course.id)

    assert first_new is True
    assert second_new is False
    assert first.id == second.id


def test_check_and_issue_certificate_withholds_until_complete(db_session):
    course, _, _subchapter, _ = make_course_with_chapter(db_session, with_quiz=False)
    user = make_user(db_session)

    certificate, newly_issued = certificate_service.check_and_issue_certificate(
        db_session, user.id, course.id
    )

    assert certificate is None
    assert newly_issued is False
