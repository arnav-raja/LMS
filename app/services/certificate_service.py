from sqlalchemy.orm import Session

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
    for any chapter with a mandatory quiz, that quiz has been passed."""
    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course_id)
        .all()
    )

    if not chapters:
        return False

    completed_subchapter_ids = get_completed_subchapter_ids(db, user_id)

    for chapter in chapters:
        subchapter_ids = {
            row.id
            for row in (
                db.query(Subchapter.id)
                .filter(Subchapter.chapter_id == chapter.id)
                .all()
            )
        }

        if not subchapter_ids.issubset(completed_subchapter_ids):
            return False

        quiz = (
            db.query(Quiz)
            .filter(Quiz.chapter_id == chapter.id)
            .first()
        )

        if quiz is not None:
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

            if not passed:
                return False

    return True


def check_and_issue_certificate(
    db: Session,
    user_id: int,
    course_id: int
) -> Certificate | None:
    """Called after any subchapter completion or quiz pass. Issues the
    certificate automatically the moment every requirement is met —
    there is no separate admin action to trigger it."""
    existing = (
        db.query(Certificate)
        .filter(
            Certificate.user_id == user_id,
            Certificate.course_id == course_id
        )
        .first()
    )

    if existing is not None:
        return existing

    if not is_course_complete(db, user_id, course_id):
        return None

    certificate = Certificate(
        user_id=user_id,
        course_id=course_id
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)

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
