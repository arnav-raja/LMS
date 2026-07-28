from sqlalchemy.orm import Session

from app.models.user import User

from app.utils.security import hash_password
from app.utils.security import verify_password

from app.services.jwt_service import create_access_token


def register_user(
    db: Session,
    name: str,
    username: str,
    email: str,
    password: str
):
    existing_email = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_email:
        raise ValueError(
            "Email already registered"
        )

    existing_username = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing_username:
        raise ValueError(
            "Username already taken"
        )

    user = User(
        name=name,
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="student"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_user(
    db: Session,
    identifier: str,
    password: str
):
    """`identifier` may be either the user's username or their email
    address, so a person can sign in with whichever they remember."""
    user = (
        db.query(User)
        .filter(
            (User.username == identifier)
            | (User.email == identifier)
        )
        .first()
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash
    ):
        return None

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return access_token