from app.models.user import User
from app.services.auth_service import login_user
from app.services.jwt_service import decode_access_token
from app.utils.security import hash_password


def make_user(db_session, **overrides):
    defaults = dict(
        name="Ada Lovelace",
        username="ada",
        email="ada@example.com",
        password_hash=hash_password("correct-horse"),
        role="student",
        department="EC",
        seniority="Mid",
    )
    defaults.update(overrides)

    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_login_with_username_succeeds(db_session):
    make_user(db_session)

    token = login_user(db_session, "ada", "correct-horse")

    assert token is not None
    payload = decode_access_token(token)
    assert payload["role"] == "student"


def test_login_with_email_succeeds(db_session):
    make_user(db_session)

    token = login_user(db_session, "ada@example.com", "correct-horse")

    assert token is not None


def test_login_with_wrong_password_fails(db_session):
    make_user(db_session)

    token = login_user(db_session, "ada", "wrong-password")

    assert token is None


def test_login_with_unknown_identifier_fails(db_session):
    token = login_user(db_session, "nobody", "whatever")

    assert token is None
