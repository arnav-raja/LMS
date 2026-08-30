from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from app.errors import NotFoundError
from app.errors import PermissionDeniedError

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

from app.utils.time import utc_now


def is_chapter_complete(
    db: Session,
    user_id: int,
    chapter_id: int,
    completed_subchapter_ids: set[int] | None = None
) -> bool:
    """Every subchapter in the chapter has been marked complete. A chapter
    with no subchapters at all counts as complete (nothing to gate on).

    Pass `completed_subchapter_ids` when checking several chapters for the
    same user in one request — it's the user's whole completion history,
    not scoped to one chapter, so it should be fetched once and reused
    rather than requeried per chapter."""
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

    if completed_subchapter_ids is None:
        completed_subchapter_ids = get_completed_subchapter_ids(db, user_id)

    return subchapter_ids.issubset(completed_subchapter_ids)


def get_course_quiz_gate_map(
    db: Session,
    user_id: int,
    course_id: int
) -> dict[int, dict]:
    """For every chapter in the course: whether it has a quiz and whether
    the user has passed it. A chapter with no quiz is treated as already
    'passed', since it should never block the chapter after it.

    Loads all of the course's quizzes and the user's passed attempts in
    one query each — this runs on every course player page load, so a
    per-chapter query here would multiply with the course's chapter count."""
    chapter_ids = [
        row.id
        for row in (
            db.query(Chapter.id)
            .filter(Chapter.course_id == course_id)
            .all()
        )
    ]

    quiz_by_chapter: dict[int, int] = {
        row.chapter_id: row.id
        for row in (
            db.query(Quiz.chapter_id, Quiz.id)
            .filter(Quiz.chapter_id.in_(chapter_ids))
            .all()
        )
    }

    passed_quiz_ids: set[int] = {
        row.quiz_id
        for row in (
            db.query(QuizAttempt.quiz_id)
            .filter(
                QuizAttempt.quiz_id.in_(quiz_by_chapter.values()),
                QuizAttempt.user_id == user_id,
                QuizAttempt.passed == True
            )
            .all()
        )
    }

    gate_map: dict[int, dict] = {}

    for chapter_id in chapter_ids:
        quiz_id = quiz_by_chapter.get(chapter_id)

        if quiz_id is None:
            gate_map[chapter_id] = {"has_quiz": False, "passed": True}
        else:
            gate_map[chapter_id] = {
                "has_quiz": True,
                "passed": quiz_id in passed_quiz_ids
            }

    return gate_map


def get_quiz_summary_for_chapter(
    db: Session,
    user_id: int,
    chapter_id: int,
    completed_subchapter_ids: set[int] | None = None
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
    is_unlocked = is_chapter_complete(
        db, user_id, chapter_id, completed_subchapter_ids
    )

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
        raise NotFoundError("Chapter not found")

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
) -> Quiz:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise NotFoundError("Quiz not found")

    return quiz


def delete_quiz(
    db: Session,
    quiz_id: int
) -> None:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise NotFoundError("Quiz not found")

    db.delete(quiz)
    db.commit()


def list_all_quizzes_admin(db: Session) -> list[dict]:
    quizzes = (
        db.query(Quiz)
        .options(
            joinedload(Quiz.chapter).joinedload(Chapter.course),
            selectinload(Quiz.attempts)
        )
        .all()
    )

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
) -> dict:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise NotFoundError("Quiz not found")

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id)
        .all()
    )

    by_user: dict[int, list] = {}

    for attempt in attempts:
        by_user.setdefault(attempt.user_id, []).append(attempt)

    users_by_id: dict[int, User] = {
        user.id: user
        for user in (
            db.query(User)
            .filter(User.id.in_(by_user.keys()))
            .all()
        )
    } if by_user else {}

    rows = []

    for user_id, user_attempts in by_user.items():
        user = users_by_id.get(user_id)

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
) -> Quiz:
    """The quiz as a student is allowed to see it, or an error explaining
    why they are not.

    A student who cannot reach the course gets the same "finish the
    chapter first" answer as one who simply has not finished it, so the
    response never reveals that a course they cannot see exists.
    """
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise NotFoundError("Quiz not found")

    chapter = quiz.chapter

    if not user.is_admin:
        if not user_has_access(db, user, chapter.course_id):
            raise PermissionDeniedError(
                "Complete every lesson in this chapter first"
            )

        if not is_chapter_complete(db, user.id, chapter.id):
            raise PermissionDeniedError(
                "Complete every lesson in this chapter first"
            )

    return quiz


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
        submitted_at=utc_now()
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
    """Loads every accessible course's chapters, quizzes, this user's
    attempts, and progress in a fixed number of queries, then assembles
    the list in memory. A per-chapter query here would multiply with the
    number of courses and chapters the user can see."""
    courses = get_accessible_courses(db, user)
    course_ids = [course.id for course in courses]

    if not course_ids:
        return []

    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id.in_(course_ids))
        .all()
    )
    chapter_ids = [chapter.id for chapter in chapters]

    quiz_by_chapter: dict[int, Quiz] = {
        quiz.chapter_id: quiz
        for quiz in (
            db.query(Quiz)
            .filter(Quiz.chapter_id.in_(chapter_ids))
            .all()
        )
    }
    quiz_ids = [quiz.id for quiz in quiz_by_chapter.values()]

    question_count_by_quiz: dict[int, int] = {
        row.quiz_id: row.count
        for row in (
            db.query(
                QuizQuestion.quiz_id,
                func.count(QuizQuestion.id).label("count")
            )
            .filter(QuizQuestion.quiz_id.in_(quiz_ids))
            .group_by(QuizQuestion.quiz_id)
            .all()
        )
    }

    attempts_by_quiz: dict[int, list[QuizAttempt]] = {}
    for attempt in (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.quiz_id.in_(quiz_ids),
            QuizAttempt.user_id == user.id
        )
        .all()
    ):
        attempts_by_quiz.setdefault(attempt.quiz_id, []).append(attempt)

    completed_subchapter_ids = get_completed_subchapter_ids(db, user.id)

    subchapters_by_chapter: dict[int, set[int]] = {
        chapter_id: set() for chapter_id in chapter_ids
    }
    for row in (
        db.query(Subchapter.chapter_id, Subchapter.id)
        .filter(Subchapter.chapter_id.in_(chapter_ids))
        .all()
    ):
        subchapters_by_chapter[row.chapter_id].add(row.id)

    chapters_by_course: dict[int, list[Chapter]] = {}
    for chapter in chapters:
        chapters_by_course.setdefault(chapter.course_id, []).append(chapter)

    items = []

    for course in courses:
        course_chapters = sorted(
            chapters_by_course.get(course.id, []),
            key=lambda c: c.chapter_number
        )

        for chapter in course_chapters:
            quiz = quiz_by_chapter.get(chapter.id)

            if quiz is None:
                continue

            is_unlocked = subchapters_by_chapter[chapter.id].issubset(
                completed_subchapter_ids
            )
            quiz_attempts = attempts_by_quiz.get(quiz.id, [])
            best_score = max((a.score for a in quiz_attempts), default=None)
            is_passed = any(a.passed for a in quiz_attempts)

            if is_passed:
                status = "passed"
            elif not is_unlocked:
                status = "locked"
            elif len(quiz_attempts) > 0:
                status = "failed"
            else:
                status = "available"

            items.append(
                {
                    "quiz_id": quiz.id,
                    "quiz_title": quiz.title,
                    "chapter_id": chapter.id,
                    "chapter_title": chapter.title,
                    "course_id": course.id,
                    "course_title": course.title,
                    "status": status,
                    "best_score": best_score,
                    "passing_score": quiz.passing_score,
                    "question_count": question_count_by_quiz.get(quiz.id, 0)
                }
            )

    return items
