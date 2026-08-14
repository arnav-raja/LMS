from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.schemas.dashboard import DashboardResponse

from app.services.dashboard_service import get_dashboard


router = APIRouter(
    prefix="/me",
    tags=["Dashboard"]
)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_dashboard(
        db=db,
        user=current_user
    )