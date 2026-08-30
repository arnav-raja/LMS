from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin
from app.dependencies.auth import get_current_user

from app.constants import DEPARTMENT_LABELS
from app.constants import Department
from app.constants import Seniority

from app.errors import ConflictError

from app.schemas.admin import AuditEntryResponse
from app.schemas.chapter import AdminChapterListItem
from app.schemas.admin import DashboardResponse
from app.schemas.admin import DepartmentOption
from app.schemas.admin import RoleOption
from app.schemas.admin import UserListItem
from app.schemas.admin import CreateUserRequest
from app.schemas.admin import UpdateUserRequest

from app.schemas.tracking import CourseRosterResponse
from app.schemas.tracking import StudentProgressResponse
from app.schemas.tracking import StudentSummary

from app.services.admin_service import get_dashboard
from app.services.audit_service import list_entries as list_audit_entries
from app.services.chapter_service import list_all_chapters_admin
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


# Static label lookups, not admin actions — every signed-in user needs these
# to render their own department/seniority (e.g. the sidebar), not just admins.
@router.get("/departments", response_model=list[DepartmentOption])
def list_departments(
    current_user = Depends(get_current_user)
):
    return [
        {"code": department, "label": DEPARTMENT_LABELS[department]}
        for department in Department
    ]


@router.get("/roles", response_model=list[RoleOption])
def list_roles(
    current_user = Depends(get_current_user)
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
    return create_user(
        db=db,
        actor=current_user,
        name=request.name,
        username=request.username,
        email=request.email,
        password=request.password,
        role=request.role.value,
        department=request.department.value if request.department else None,
        seniority=request.seniority.value if request.seniority else None
    )


@router.patch("/users/{user_id}", response_model=UserListItem)
def edit_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return update_user(
        db=db,
        actor=current_user,
        user_id=user_id,
        name=request.name,
        username=request.username,
        email=request.email,
        password=request.password,
        role=request.role.value if request.role else None,
        department=request.department.value if request.department else None,
        seniority=request.seniority.value if request.seniority else None,
        # Tells the service which fields the caller actually sent, so a
        # PATCH that omits `department` leaves it alone while one that
        # sends `null` genuinely clears it.
        provided_fields=request.model_fields_set
    )


@router.delete("/users/{user_id}")
def remove_user(
    user_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if current_user.id == user_id:
        raise ConflictError("You cannot delete your own account")

    # `removed` says what went with the account — progress, quiz attempts
    # and certificates all cascade. The admin is told, because a deleted
    # certificate is a deleted record of something someone earned.
    removed = delete_user(db, current_user, user_id)

    return {"deleted": True, "removed": removed}


@router.get("/chapters", response_model=list[AdminChapterListItem])
def all_chapters(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Every chapter with its course, for the quiz builder's picker.

    One request. The Quizzes page used to assemble this by asking the
    course player's endpoint once per course.
    """
    return list_all_chapters_admin(db)


@router.get("/audit", response_model=list[AuditEntryResponse])
def audit_log(
    limit: int = 100,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Recent administrative actions on accounts, newest first.

    Admin-only, and append-only: there is no route that edits or removes
    an entry, deliberately.
    """
    return list_audit_entries(db, limit=min(limit, 500))


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
    return get_student_progress_detail(db, user_id)


@router.get(
    "/courses/{course_id}/students",
    response_model=CourseRosterResponse
)
def course_students(
    course_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return get_course_roster(db, course_id)
