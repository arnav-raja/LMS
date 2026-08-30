from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.course import CourseResponse

from app.services.access_service import get_accessible_courses
from app.services.course_service import archive_course
from app.services.course_service import get_courses
from app.services.course_service import publish_course


router = APIRouter(
    prefix="/courses",
    tags=["Courses"]
)


@router.get("", response_model=list[CourseResponse])
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.is_admin:
        return get_courses(db)

    return get_accessible_courses(db, current_user)


@router.post("/{course_id}/publish", response_model=CourseResponse)
def publish(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return publish_course(
        db=db,
        course_id=course_id
    )


@router.post("/{course_id}/archive", response_model=CourseResponse)
def archive(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return archive_course(
        db=db,
        course_id=course_id
    )
