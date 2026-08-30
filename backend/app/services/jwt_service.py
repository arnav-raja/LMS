from datetime import timedelta

from jose import JWTError
from jose import jwt

from app.config import SECRET_KEY
from app.config import ALGORITHM
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

from app.utils.time import utc_now


def create_access_token(data: dict):
    payload = data.copy()

    expire = (
        utc_now()
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None
