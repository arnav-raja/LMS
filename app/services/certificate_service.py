from io import BytesIO
from pathlib import Path

from jinja2 import Environment
from jinja2 import FileSystemLoader

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from weasyprint import HTML

from pdf2image import convert_from_bytes

from app.models.certificate import Certificate
from app.models.chapter import Chapter
from app.models.quiz import Quiz
from app.models.quiz import QuizAttempt
from app.models.subchapter import Subchapter

from app.services.progress_service import get_completed_subchapter_ids


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR)
)


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


def get_certificate_by_id(
    db: Session,
    certificate_id: int
) -> Certificate | None:
    return (
        db.query(Certificate)
        .options(
            joinedload(Certificate.user),
            joinedload(Certificate.course)
        )
        .filter(Certificate.id == certificate_id)
        .first()
    )


def _render_certificate_html(certificate: Certificate) -> str:
    """Fills the single certificate template with this certificate's own
    student name and course title — the same template renders every
    certificate ever issued, so there is nothing else to keep in sync."""
    template = _jinja_env.get_template("certificate.html")

    return template.render(
        student_name=certificate.user.name,
        course_title=certificate.course.title,
        issued_at=certificate.issued_at.strftime("%d %B %Y"),
        certificate_number=certificate.certificate_number
    )


def render_certificate_pdf(certificate: Certificate) -> bytes:
    html = _render_certificate_html(certificate)

    return HTML(string=html).write_pdf()


def render_certificate_png(certificate: Certificate) -> bytes:
    """Renders the same PDF as render_certificate_pdf, then rasterises its
    single page to PNG, so the PDF and image downloads can never drift
    apart in layout."""
    pdf_bytes = render_certificate_pdf(certificate)

    pages = convert_from_bytes(pdf_bytes, dpi=200)

    buffer = BytesIO()
    pages[0].save(buffer, format="PNG")

    return buffer.getvalue()
