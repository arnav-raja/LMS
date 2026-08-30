from fastapi import Depends
from fastapi import HTTPException

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.database import get_db

from app.models.user import User

from app.services.jwt_service import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# One message for every way a token can fail, so a caller cannot learn
# from the response whether an account exists, whether it was deleted, or
# whether their token was merely revoked.
INVALID_CREDENTIALS = "Could not validate credentials"


def _reject():
    raise HTTPException(
        status_code=401,
        detail=INVALID_CREDENTIALS
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)

    if payload is None:
        _reject()

    user_id = payload.get("sub")

    if user_id is None:
        _reject()

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        # `sub` is attacker-controlled in the sense that a forged token
        # could carry anything; int() on it used to raise ValueError and
        # surface as a 500.
        _reject()

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        _reject()

    # A token issued before the account's password or role last changed is
    # no longer valid, even though it has not expired yet. Tokens minted
    # before this claim existed carry no `tv` and are rejected outright,
    # which signs everyone out once, on the deploy that introduces it.
    if payload.get("tv") != user.token_version:
        _reject()

    return user
