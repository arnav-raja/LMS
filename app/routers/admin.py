from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin

from app.constants import DEPARTMENT_LABELS
from app.constants import Department
from app.constants import Seniority

from app.schemas.admin import DashboardResponse
from app.schemas.admin import DepartmentOption
from app.schemas.admin import RoleOption
from app.schemas.admin import UserAccessProfileUpdate
from app.schemas.admin import UserListItem
from app.schemas.admin import CreateUserRequest
from app.schemas.admin import UpdateUserRequest

from app.schemas.auth import UserResponse

from app.schemas.tracking import CourseRosterResponse
from app.schemas.tracking import StudentProgressResponse
from app.schemas.tracking import StudentSummary

from app.services.admin_service import get_dashboard
from app.services.admin_service import update_user_access_profile
from app.services.admin_service import list_all_users
from app.services.admin_service import create_user
from app.services.admin_service import update_user
from app.services.admin_service import delete_user
from app.services.tracking_service import get_course_roster
from app.services.tracking_service import get_student_progress_detail
from app.services.tracking_service import list_students


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return get_dashboard(db)


@router.get("/departments", response_model=list[DepartmentOption])
def list_departments(
    current_user = Depends(require_admin)
):
    return [
        {"code": department, "label": DEPARTMENT_LABELS[department]}
        for department in Department
    ]


@router.get("/roles", response_model=list[RoleOption])
def list_roles(
    current_user = Depends(require_admin)
):
    return [{"value": seniority} for seniority in Seniority]


@router.get("/users", response_model=list[UserListItem])
def get_users(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return list_all_users(db)


@router.post("/users", response_model=UserListItem)
def add_user(
    request: CreateUserRequest,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        return create_user(
            db=db,
            name=request.name,
            username=request.username,
            email=request.email,
            password=request.password,
            role=request.role,
            department=request.department.value if request.department else None,
            seniority=request.seniority.value if request.seniority else None
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.patch("/users/{user_id}", response_model=UserListItem)
def edit_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        user = update_user(
            db=db,
            user_id=user_id,
            name=request.name,
            username=request.username,
            email=request.email,
            password=request.password,
            role=request.role,
            department=request.department.value if request.department else None,
            seniority=request.seniority.value if request.seniority else None
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.delete("/users/{user_id}")
def remove_user(
    user_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account"
        )

    deleted = delete_user(db, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {"deleted": True}


@router.patch("/users/{user_id}/access-profile", response_model=UserResponse)
def set_user_access_profile(
    user_id: int,
    request: UserAccessProfileUpdate,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = update_user_access_profile(
        db=db,
        user_id=user_id,
        department=request.department.value,
        seniority=request.seniority.value
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.get("/students", response_model=list[StudentSummary])
def students(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return list_students(db)


@router.get(
    "/students/{user_id}/progress",
    response_model=StudentProgressResponse
)
def student_progress(
    user_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    result = get_student_progress_detail(db, user_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return result


@router.get(
    "/courses/{course_id}/students",
    response_model=CourseRosterResponse
)
def course_students(
    course_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    result = get_course_roster(db, course_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    return result