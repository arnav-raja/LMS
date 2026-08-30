from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin

from app.models.user import User

from app.schemas.course import CourseResponse
from app.schemas.course_builder import CreateCourseRequest

from app.services.course_builder_service import create_course
from app.services.course_builder_service import update_course
from app.services.course_builder_service import delete_course


router = APIRouter(
    prefix="/admin/courses",
    tags=["Course Builder"]
)


@router.post("", response_model=CourseResponse)
def create(
    request: CreateCourseRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return create_course(
        db=db,
        request=request
    )


@router.put("/{course_id}", response_model=CourseResponse)
def update(
    course_id: int,
    request: CreateCourseRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return update_course(
        db=db,
        course_id=course_id,
        request=request
    )


@router.delete("/{course_id}")
def delete(
    course_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    delete_course(
        db=db,
        course_id=course_id
    )

    return {
        "message": "Course deleted successfully"
    }
