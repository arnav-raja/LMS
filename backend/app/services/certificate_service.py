from sqlalchemy.orm import Session

from app.errors import NotFoundError

from app.models.certificate import Certificate
from app.models.chapter import Chapter
from app.models.quiz import Quiz
from app.models.quiz import QuizAttempt
from app.models.subchapter import Subchapter

from app.services.progress_service import get_completed_subchapter_ids


def is_course_complete(
    db: Session,
    user_id: int,
    course_id: int
) -> bool:
    """A course is complete once every chapter's subchapters are done and,
    for any chapter with a mandatory quiz, that quiz has been passed.

    Loads every chapter's subchapters, quizzes, and the user's passed
    attempts in one query each, rather than once per chapter — this is
    called after every subchapter completion and quiz submission."""
    chapter_ids = [
        row.id
        for row in (
            db.query(Chapter.id)
            .filter(Chapter.course_id == course_id)
            .all()
        )
    ]

    if not chapter_ids:
        return False

    completed_subchapter_ids = get_completed_subchapter_ids(db, user_id)

    subchapters_by_chapter: dict[int, set[int]] = {
        chapter_id: set() for chapter_id in chapter_ids
    }
    for row in (
        db.query(Subchapter.chapter_id, Subchapter.id)
        .filter(Subchapter.chapter_id.in_(chapter_ids))
        .all()
    ):
        subchapters_by_chapter[row.chapter_id].add(row.id)

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

    for chapter_id in chapter_ids:
        if not subchapters_by_chapter[chapter_id].issubset(completed_subchapter_ids):
            return False

        quiz_id = quiz_by_chapter.get(chapter_id)

        if quiz_id is not None and quiz_id not in passed_quiz_ids:
            return False

    return True


def check_and_issue_certificate(
    db: Session,
    user_id: int,
    course_id: int
) -> tuple[Certificate | None, bool]:
    """Called after any subchapter completion or quiz pass. Issues the
    certificate automatically the moment every requirement is met —
    there is no separate admin action to trigger it.

    Returns (certificate, was_newly_issued). The caller needs to know
    whether this specific call is what earned the certificate, so it
    can show a "you've just earned this" moment rather than treating an
    already-existing certificate the same way."""
    existing = (
        db.query(Certificate)
        .filter(
            Certificate.user_id == user_id,
            Certificate.course_id == course_id
        )
        .first()
    )

    if existing is not None:
        return existing, False

    if not is_course_complete(db, user_id, course_id):
        return None, False

    certificate = Certificate(
        user_id=user_id,
        course_id=course_id
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    return certificate, True


def verify_certificate(
    db: Session,
    certificate_number: str
) -> Certificate:
    """Look up a certificate by the number printed on it.

    This backs the one public, unauthenticated route in the application:
    somebody handed a certificate needs to be able to check it without an
    account here. The number is 64 bits of randomness, so it cannot be
    guessed or walked — but it is also the only thing protecting the
    lookup, which is why the response carries as little as it does.

    A number that does not exist and one that is malformed both come back
    as the same "not found", so the endpoint cannot be used to learn
    anything about which numbers have been issued.
    """
    certificate = (
        db.query(Certificate)
        .filter(Certificate.certificate_number == certificate_number.strip())
        .first()
    )

    if certificate is None:
        raise NotFoundError("No certificate found with that number")

    return certificate


def get_user_certificates(
    db: Session,
    user_id: int
) -> list[Certificate]:
    return (
        db.query(Certificate)
        .filter(Certificate.user_id == user_id)
        .order_by(Certificate.issued_at.desc())
        .all()
    )


def list_all_certificates(
    db: Session,
    course_id: int | None = None
) -> list[Certificate]:
    query = db.query(Certificate)

    if course_id is not None:
        query = query.filter(Certificate.course_id == course_id)

    return query.order_by(Certificate.issued_at.desc()).all()
