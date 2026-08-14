from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin

from app.models.user import User

from app.schemas.access import GrantAccessRequest
from app.schemas.access import CourseAccessRuleResponse

from app.services.access_service import grant_access
from app.services.access_service import revoke_access
from app.services.access_service import get_course_access_rules
from app.services.course_service import get_course


router = APIRouter(
    prefix="/admin/courses/{course_id}/access",
    tags=["Course Access"]
)


def _ensure_course_exists(db: Session, course_id: int):
    if get_course(db, course_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )


@router.get("", response_model=list[CourseAccessRuleResponse])
def list_access(
    course_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    _ensure_course_exists(db, course_id)

    return get_course_access_rules(db, course_id)


@router.post("", response_model=CourseAccessRuleResponse)
def grant(
    course_id: int,
    request: GrantAccessRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    _ensure_course_exists(db, course_id)

    return grant_access(
        db=db,
        course_id=course_id,
        department=request.department.value,
        seniority=request.seniority.value
    )


@router.delete("")
def revoke(
    course_id: int,
    request: GrantAccessRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    _ensure_course_exists(db, course_id)

    revoked = revoke_access(
        db=db,
        course_id=course_id,
        department=request.department.value,
        seniority=request.seniority.value
    )

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail="Access rule not found"
        )

    return {
        "message": "Access revoked"
    }
