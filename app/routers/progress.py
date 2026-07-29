from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.progress import CompleteSubchapterRequest
from app.schemas.progress import ProgressResponse

from app.services.access_service import user_has_access
from app.services.certificate_service import check_and_issue_certificate
from app.services.progress_service import complete_subchapter
from app.services.progress_service import get_subchapter_course_id
from app.services.progress_service import get_user_progress
from app.services.sequence_service import is_subchapter_unlocked


router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)


@router.post("/complete", response_model=ProgressResponse)
def complete(
    request: CompleteSubchapterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course_id = get_subchapter_course_id(
        db,
        request.subchapter_id
    )

    if course_id is None:
        raise HTTPException(
            status_code=404,
            detail="Subchapter not found"
        )

    if not user_has_access(db, current_user, course_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this course"
        )

    if current_user.role != "admin" and not is_subchapter_unlocked(
        db,
        current_user.id,
        course_id,
        request.subchapter_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Complete the previous subchapter first"
        )

    result = complete_subchapter(
        db=db,
        user_id=current_user.id,
        subchapter_id=request.subchapter_id
    )

    # A course with no quizzes at all becomes complete the moment its last
    # subchapter is marked done, so this check has to run here too, not
    # only after a quiz submission.
    _, certificate_issued = check_and_issue_certificate(
        db=db,
        user_id=current_user.id,
        course_id=course_id
    )

    return {
        "id": result.id,
        "user_id": result.user_id,
        "subchapter_id": result.subchapter_id,
        "is_completed": result.is_completed,
        "certificate_issued": certificate_issued,
    }


@router.get("/me", response_model=list[ProgressResponse])
def my_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_progress(
        db=db,
        user_id=current_user.id
    )
