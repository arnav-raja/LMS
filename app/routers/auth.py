from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import TokenResponse
from app.schemas.auth import UserResponse
from app.services.auth_service import login_user
from app.dependencies.auth import get_current_user
from app.models.user import User
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# There is deliberately no self-service registration route. Every account —
# student or admin — is created by an administrator from the Students page
# (see app/routers/admin.py: create_user / update_user / delete_user).

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # OAuth2PasswordRequestForm calls this field "username", but we accept
    # either the account's username or its email address in it.
    token = login_user(
        db=db,
        identifier=form_data.username,
        password=form_data.password
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user)
):
    return current_user
