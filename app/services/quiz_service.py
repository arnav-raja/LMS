from datetime import datetime

from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.quiz import Quiz
from app.models.quiz import QuizAnswer
from app.models.quiz import QuizAttempt
from app.models.quiz import QuizOption
from app.models.quiz import QuizQuestion
from app.models.subchapter import Subchapter
from app.models.user import User

from app.services.access_service import get_accessible_courses
from app.services.access_service import user_has_access
from app.services.progress_service import get_completed_subchapter_ids


def is_chapter_complete(
    db: Session,
    user_id: int,
    chapter_id: int
) -> bool:
    """Every subchapter in the chapter has been marked complete. A chapter
    with no subchapters at all counts as complete (nothing to gate on)."""
    subchapter_ids = {
        row.id
        for row in (
            db.query(Subchapter.id)
            .filter(Subchapter.chapter_id == chapter_id)
            .all()
        )
    }

    if not subchapter_ids:
        return True

    completed_ids = get_completed_subchapter_ids(db, user_id)

    return subchapter_ids.issubset(completed_ids)


def get_course_quiz_gate_map(
    db: Session,
    user_id: int,
    course_id: int
) -> dict[int, dict]:
    """For every chapter in the course: whether it has a quiz and whether
    the user has passed it. A chapter with no quiz is treated as already
    'passed', since it should never block the chapter after it."""
    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course_id)
        .all()
    )

    gate_map: dict[int, dict] = {}

    for chapter in chapters:
        quiz = (
            db.query(Quiz)
            .filter(Quiz.chapter_id == chapter.id)
            .first()
        )

        if quiz is None:
            gate_map[chapter.id] = {"has_quiz": False, "passed": True}
            continue

        passed = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.user_id == user_id,
                QuizAttempt.passed == True
            )
            .first()
            is not None
        )

        gate_map[chapter.id] = {"has_quiz": True, "passed": passed}

    return gate_map


def get_quiz_summary_for_chapter(
    db: Session,
    user_id: int,
    chapter_id: int
) -> dict | None:
    quiz = (
        db.query(Quiz)
        .filter(Quiz.chapter_id == chapter_id)
        .first()
    )

    if quiz is None:
        return None

    attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.quiz_id == quiz.id,
            QuizAttempt.user_id == user_id
        )
        .all()
    )

    best_score = max((attempt.score for attempt in attempts), default=None)
    is_passed = any(attempt.passed for attempt in attempts)
    is_unlocked = is_chapter_complete(db, user_id, chapter_id)

    return {
        "id": quiz.id,
        "title": quiz.title,
        "passing_score": quiz.passing_score,
        "is_unlocked": is_unlocked,
        "is_passed": is_passed,
        "best_score": best_score,
        "attempts_count": len(attempts)
    }


# --------------------------------------------------------------- admin ----

def create_or_replace_quiz(
    db: Session,
    chapter_id: int,
    request
) -> Quiz:
    """A chapter has exactly one quiz. Saving from the builder replaces
    it wholesale, which also clears any previous attempts recorded
    against the old version — the questions are different now."""
    chapter = db.get(Chapter, chapter_id)

    if chapter is None:
        raise ValueError("Chapter not found")

    existing = (
        db.query(Quiz)
        .filter(Quiz.chapter_id == chapter_id)
        .first()
    )

    if existing is not None:
        db.delete(existing)
        db.flush()

    quiz = Quiz(
        chapter_id=chapter_id,
        title=request.title,
        passing_score=request.passing_score
    )

    db.add(quiz)
    db.flush()

    for question_index, question_data in enumerate(
        request.questions,
        start=1
    ):
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_number=question_index,
            question_text=question_data.question_text
        )

        db.add(question)
        db.flush()

        for option_data in question_data.options:
            db.add(
                QuizOption(
                    question_id=question.id,
                    option_text=option_data.option_text,
                    is_correct=option_data.is_correct
                )
            )

    db.commit()
    db.refresh(quiz)

    return quiz


def get_quiz_admin_view(
    db: Session,
    quiz_id: int
) -> Quiz | None:
    return db.get(Quiz, quiz_id)


def delete_quiz(
    db: Session,
    quiz_id: int
) -> bool:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        return False

    db.delete(quiz)
    db.commit()

    return True


def list_all_quizzes_admin(db: Session) -> list[dict]:
    quizzes = db.query(Quiz).all()

    results = []

    for quiz in quizzes:
        chapter = quiz.chapter
        course = chapter.course
        attempts = quiz.attempts

        best_by_user: dict[int, float] = {}
        passed_users: set[int] = set()

        for attempt in attempts:
            best_by_user[attempt.user_id] = max(
                best_by_user.get(attempt.user_id, 0),
                attempt.score
            )
            if attempt.passed:
                passed_users.add(attempt.user_id)

        results.append(
            {
                "quiz_id": quiz.id,
                "quiz_title": quiz.title,
                "chapter_id": chapter.id,
                "chapter_title": chapter.title,
                "course_id": course.id,
                "course_title": course.title,
                "passing_score": quiz.passing_score,
                "question_count": len(quiz.questions),
                "attempts_count": len(best_by_user),
                "pass_count": len(passed_users)
            }
        )

    return results


def get_quiz_results_admin(
    db: Session,
    quiz_id: int
) -> dict | None:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        return None

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id)
        .all()
    )

    by_user: dict[int, list] = {}

    for attempt in attempts:
        by_user.setdefault(attempt.user_id, []).append(attempt)

    rows = []

    for user_id, user_attempts in by_user.items():
        user = db.get(User, user_id)

        rows.append(
            {
                "user_id": user_id,
                "user_name": user.name if user else "Unknown",
                "attempts_count": len(user_attempts),
                "best_score": max(a.score for a in user_attempts),
                "passed": any(a.passed for a in user_attempts)
            }
        )

    return {
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "rows": rows
    }


# ------------------------------------------------------------- student ----

def get_quiz_take_view(
    db: Session,
    user: User,
    quiz_id: int
):
    """Returns (quiz, None) on success, or (None, reason) where reason is
    'not_found' or 'locked'."""
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        return None, "not_found"

    chapter = quiz.chapter
    course_id = chapter.course_id

    if not user.is_admin:
        if not user_has_access(db, user, course_id):
            return None, "locked"

        if not is_chapter_complete(db, user.id, chapter.id):
            return None, "locked"

    return quiz, None


def submit_quiz(
    db: Session,
    user_id: int,
    quiz_id: int,
    answers
) -> QuizAttempt:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise ValueError("Quiz not found")

    questions = quiz.questions

    correct_option_by_question = {
        question.id: next(
            (option.id for option in question.options if option.is_correct),
            None
        )
        for question in questions
    }

    selected_by_question = {
        answer.question_id: answer.option_id
        for answer in answers
    }

    attempt = QuizAttempt(
        user_id=user_id,
        quiz_id=quiz_id,
        score=0,
        passed=False,
        submitted_at=datetime.utcnow()
    )

    db.add(attempt)
    db.flush()

    correct_count = 0
    total = len(questions)

    for question in questions:
        selected_option_id = selected_by_question.get(question.id)

        if (
            selected_option_id is not None
            and selected_option_id == correct_option_by_question.get(question.id)
        ):
            correct_count += 1

        db.add(
            QuizAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=selected_option_id
            )
        )

    score = round((correct_count / total) * 100, 2) if total > 0 else 0
    passed = score >= quiz.passing_score

    attempt.score = score
    attempt.passed = passed

    db.commit()
    db.refresh(attempt)

    return attempt


def get_student_quiz_list(
    db: Session,
    user: User
) -> list[dict]:
    courses = get_accessible_courses(db, user)

    items = []

    for course in courses:
        for chapter in sorted(course.chapters, key=lambda c: c.chapter_number):
            summary = get_quiz_summary_for_chapter(db, user.id, chapter.id)

            if summary is None:
                continue

            if summary["is_passed"]:
                status = "passed"
            elif not summary["is_unlocked"]:
                status = "locked"
            elif summary["attempts_count"] > 0:
                status = "failed"
            else:
                status = "available"

            items.append(
                {
                    "quiz_id": summary["id"],
                    "quiz_title": summary["title"],
                    "chapter_id": chapter.id,
                    "chapter_title": chapter.title,
                    "course_id": course.id,
                    "course_title": course.title,
                    "status": status,
                    "best_score": summary["best_score"],
                    "passing_score": summary["passing_score"],
                    "question_count": len(chapter.quiz.questions) if chapter.quiz else 0
                }
            )

    return items
