from app.models.chapter import Chapter
from app.models.course import Course
from app.models.quiz import Quiz
from app.models.quiz import QuizAttempt
from app.models.quiz import QuizOption
from app.models.quiz import QuizQuestion
from app.models.subchapter import Subchapter
from app.models.user import User
from app.services import access_service
from app.services import progress_service
from app.services import quiz_service
from app.utils.security import hash_password


def make_user(db_session, role="student", department="EC", seniority="Mid"):
    user = User(
        name="Ada Lovelace",
        username="ada",
        email="ada@example.com",
        password_hash=hash_password("x"),
        role=role,
        department=department,
        seniority=seniority,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def make_chapter_with_quiz(db_session, course, chapter_number, question_count=2):
    chapter = Chapter(course_id=course.id, chapter_number=chapter_number, title=f"Chapter {chapter_number}")
    db_session.add(chapter)
    db_session.commit()

    subchapter = Subchapter(chapter_id=chapter.id, subchapter_number=1, title="Lesson 1")
    db_session.add(subchapter)
    db_session.commit()
    db_session.refresh(subchapter)

    quiz = Quiz(chapter_id=chapter.id, title=f"Chapter {chapter_number} Quiz", passing_score=70)
    db_session.add(quiz)
    db_session.commit()
    db_session.refresh(quiz)

    for i in range(question_count):
        question = QuizQuestion(quiz_id=quiz.id, question_number=i + 1, question_text=f"Q{i + 1}")
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)

        db_session.add(QuizOption(question_id=question.id, option_text="Right", is_correct=True))
        db_session.add(QuizOption(question_id=question.id, option_text="Wrong", is_correct=False))
        db_session.commit()

    return chapter, subchapter, quiz


def make_two_chapter_course(db_session):
    course = Course(title="Onboarding", description="Intro", status="published")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    chapter1, subchapter1, quiz1 = make_chapter_with_quiz(db_session, course, 1)
    chapter2, subchapter2, quiz2 = make_chapter_with_quiz(db_session, course, 2)

    return course, (chapter1, subchapter1, quiz1), (chapter2, subchapter2, quiz2)


def test_gate_map_chapter_without_quiz_is_treated_as_passed(db_session):
    course = Course(title="Onboarding", description="Intro", status="published")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    chapter = Chapter(course_id=course.id, chapter_number=1, title="Chapter 1")
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)

    user = make_user(db_session)

    gate_map = quiz_service.get_course_quiz_gate_map(db_session, user.id, course.id)

    assert gate_map[chapter.id] == {"has_quiz": False, "passed": True}


def test_gate_map_reflects_pass_state_per_chapter(db_session):
    course, (chapter1, subchapter1, quiz1), (chapter2, subchapter2, quiz2) = (
        make_two_chapter_course(db_session)
    )
    user = make_user(db_session)

    db_session.add(QuizAttempt(user_id=user.id, quiz_id=quiz1.id, score=100, passed=True))
    db_session.add(QuizAttempt(user_id=user.id, quiz_id=quiz2.id, score=50, passed=False))
    db_session.commit()

    gate_map = quiz_service.get_course_quiz_gate_map(db_session, user.id, course.id)

    assert gate_map[chapter1.id] == {"has_quiz": True, "passed": True}
    assert gate_map[chapter2.id] == {"has_quiz": True, "passed": False}


def test_is_chapter_complete_matches_with_and_without_precomputed_set(db_session):
    course, (chapter1, subchapter1, quiz1), _ = make_two_chapter_course(db_session)
    user = make_user(db_session)

    progress_service.complete_subchapter(db_session, user.id, subchapter1.id)
    completed_ids = progress_service.get_completed_subchapter_ids(db_session, user.id)

    without_precomputed = quiz_service.is_chapter_complete(db_session, user.id, chapter1.id)
    with_precomputed = quiz_service.is_chapter_complete(
        db_session, user.id, chapter1.id, completed_ids
    )

    assert without_precomputed is True
    assert with_precomputed is True


def test_student_quiz_list_orders_by_chapter_and_reflects_status(db_session):
    course, (chapter1, subchapter1, quiz1), (chapter2, subchapter2, quiz2) = (
        make_two_chapter_course(db_session)
    )
    student = make_user(db_session, department="EC", seniority="Mid")
    access_service.grant_access(db_session, course.id, "EC", "Mid")

    # Chapter 1 is done and its quiz passed; chapter 2's subchapter is not
    # done yet, so its quiz should read as locked with no attempts.
    progress_service.complete_subchapter(db_session, student.id, subchapter1.id)
    db_session.add(QuizAttempt(user_id=student.id, quiz_id=quiz1.id, score=90, passed=True))
    db_session.commit()

    items = quiz_service.get_student_quiz_list(db_session, student)

    assert [item["chapter_id"] for item in items] == [chapter1.id, chapter2.id]

    first, second = items

    assert first["status"] == "passed"
    assert first["best_score"] == 90
    assert first["question_count"] == 2

    assert second["status"] == "locked"
    assert second["best_score"] is None
    assert second["question_count"] == 2


def test_student_quiz_list_skips_chapters_without_a_quiz(db_session):
    course = Course(title="Onboarding", description="Intro", status="published")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    chapter = Chapter(course_id=course.id, chapter_number=1, title="No Quiz Chapter")
    db_session.add(chapter)
    db_session.commit()

    student = make_user(db_session, department="EC", seniority="Mid")
    access_service.grant_access(db_session, course.id, "EC", "Mid")

    items = quiz_service.get_student_quiz_list(db_session, student)

    assert items == []
