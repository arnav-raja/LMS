from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.auth import get_current_user

from app.errors import PermissionDeniedError

from app.models.user import User

from app.schemas.learning import ContinueLearningResponse
from app.schemas.learning import CourseProgressResponse

from app.services.access_service import user_has_access
from app.services.learning_service import continue_learning
from app.services.learning_service import get_course_progress


router = APIRouter(
    prefix="/learning",
    tags=["Learning"]
)


def _require_course_access(db: Session, user: User, course_id: int) -> None:
    if not user_has_access(db, user, course_id):
        raise PermissionDeniedError("You do not have access to this course")


@router.get("/courses/{course_id}/continue", response_model=ContinueLearningResponse)
def continue_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _require_course_access(db, current_user, course_id)

    return continue_learning(
        db=db,
        user_id=current_user.id,
        course_id=course_id
    )


@router.get("/courses/{course_id}/progress", response_model=CourseProgressResponse)
def course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _require_course_access(db, current_user, course_id)

    return get_course_progress(
        db=db,
        user_id=current_user.id,
        course_id=course_id
    )
