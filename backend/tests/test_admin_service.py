from app.models.user import User
from app.services.admin_service import update_user
from app.utils.security import hash_password


def make_user(db_session):
    user = User(
        name="Ada Lovelace",
        username="ada",
        email="ada@example.com",
        password_hash=hash_password("password"),
        role="student",
        department="EC",
        seniority="Mid",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_update_user_can_clear_optional_profile_fields(db_session):
    user = make_user(db_session)

    updated = update_user(
        db=db_session,
        user_id=user.id,
        name=None,
        username=None,
        email=None,
        password=None,
        role=None,
        department=None,
        seniority=None,
        provided_fields={"email", "department", "seniority"},
    )

    assert updated.email is None
    assert updated.department is None
    assert updated.seniority is None


def test_update_user_preserves_omitted_profile_fields(db_session):
    user = make_user(db_session)

    updated = update_user(
        db=db_session,
        user_id=user.id,
        name="Ada Byron",
        username=None,
        email=None,
        password=None,
        role=None,
        department=None,
        seniority=None,
        provided_fields={"name"},
    )

    assert updated.name == "Ada Byron"
    assert updated.email == "ada@example.com"
    assert updated.department == "EC"
    assert updated.seniority == "Mid"
