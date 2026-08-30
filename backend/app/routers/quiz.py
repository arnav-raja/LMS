from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.quiz import AdminQuizListItem
from app.schemas.quiz import QuizAdminResponse
from app.schemas.quiz import QuizAttemptResponse
from app.schemas.quiz import QuizBuilderRequest
from app.schemas.quiz import QuizListItem
from app.schemas.quiz import QuizResultsResponse
from app.schemas.quiz import QuizTakeResponse
from app.schemas.quiz import SubmitQuizRequest

from app.services import quiz_service
from app.services.certificate_service import check_and_issue_certificate


router = APIRouter(tags=["Quizzes"])


# ------------------------------------------------------- admin: builder ---

@router.post(
    "/admin/chapters/{chapter_id}/quiz",
    response_model=QuizAdminResponse
)
def create_quiz(
    chapter_id: int,
    request: QuizBuilderRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return quiz_service.create_or_replace_quiz(
        db=db,
        chapter_id=chapter_id,
        request=request
    )


@router.get("/admin/quizzes", response_model=list[AdminQuizListItem])
def list_quizzes(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return quiz_service.list_all_quizzes_admin(db)


@router.get("/admin/quizzes/{quiz_id}", response_model=QuizAdminResponse)
def get_quiz_admin(
    quiz_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return quiz_service.get_quiz_admin_view(db, quiz_id)


@router.delete("/admin/quizzes/{quiz_id}")
def remove_quiz(
    quiz_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    quiz_service.delete_quiz(db, quiz_id)

    return {"deleted": True}


@router.get(
    "/admin/quizzes/{quiz_id}/results",
    response_model=QuizResultsResponse
)
def quiz_results(
    quiz_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return quiz_service.get_quiz_results_admin(db, quiz_id)


# ----------------------------------------------------- student: attempt ---

@router.get("/quizzes/me", response_model=list[QuizListItem])
def my_quizzes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return quiz_service.get_student_quiz_list(db, current_user)


@router.get("/quizzes/{quiz_id}", response_model=QuizTakeResponse)
def take_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz = quiz_service.get_quiz_take_view(db, current_user, quiz_id)

    return {
        "id": quiz.id,
        "chapter_id": quiz.chapter_id,
        "course_id": quiz.chapter.course_id,
        "title": quiz.title,
        "passing_score": quiz.passing_score,
        "questions": quiz.questions,
    }


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizAttemptResponse)
def submit_quiz(
    quiz_id: int,
    request: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Same gate as viewing it — a locked quiz cannot be submitted either.
    quiz = quiz_service.get_quiz_take_view(db, current_user, quiz_id)

    attempt = quiz_service.submit_quiz(
        db=db,
        user_id=current_user.id,
        quiz_id=quiz_id,
        answers=request.answers
    )

    certificate_issued = False

    if attempt.passed:
        # A passed quiz may be the last requirement for the course —
        # check whether a certificate should now be issued.
        _, certificate_issued = check_and_issue_certificate(
            db=db,
            user_id=current_user.id,
            course_id=quiz.chapter.course_id
        )

    return {
        "id": attempt.id,
        "quiz_id": attempt.quiz_id,
        "score": attempt.score,
        "passed": attempt.passed,
        "submitted_at": attempt.submitted_at,
        "course_id": quiz.chapter.course_id,
        "certificate_issued": certificate_issued,
    }
