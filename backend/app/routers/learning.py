from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.auth import get_current_user

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


@router.get("/courses/{course_id}/continue", response_model=ContinueLearningResponse)
def continue_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not user_has_access(db, current_user, course_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this course"
        )

    lesson = continue_learning(
        db=db,
        user_id=current_user.id,
        course_id=course_id
    )

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Course completed"
        )

    return lesson


@router.get("/courses/{course_id}/progress", response_model=CourseProgressResponse)
def course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not user_has_access(db, current_user, course_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this course"
        )

    return get_course_progress(
        db=db,
        user_id=current_user.id,
        course_id=course_id
    )
