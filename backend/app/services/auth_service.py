from sqlalchemy.orm import Session

from app.models.user import User

from app.utils.security import verify_password

from app.services.jwt_service import create_access_token
from app.services.login_guard import check_not_locked_out
from app.services.login_guard import record_attempt


def login_user(
    db: Session,
    identifier: str,
    password: str
):
    """`identifier` may be either the user's username or their email
    address, so a person can sign in with whichever they remember.

    Returns the token, or None if the credentials are wrong. Raises
    TooManyAttemptsError if this identifier has been guessed at too often
    — checked before the password comparison, so a locked-out caller gets
    nothing back, not even the timing of a bcrypt hash.
    """
    check_not_locked_out(db, identifier)

    user = (
        db.query(User)
        .filter(
            (User.username == identifier)
            | (User.email == identifier)
        )
        .first()
    )

    if user is None:
        record_attempt(db, identifier, succeeded=False)
        return None

    if not verify_password(
        password,
        user.password_hash
    ):
        record_attempt(db, identifier, succeeded=False)
        return None

    record_attempt(db, identifier, succeeded=True)

    return issue_token_for(user)


def issue_token_for(user: User) -> str:
    """The access token for an account.

    `role` is carried for convenience only — every request re-reads the
    user from the database, so a role change takes effect immediately and
    the claim is never trusted for a permission decision.

    `tv` is the account's token_version, and it *is* trusted: a request
    whose token carries a stale one is rejected. That is what makes a
    password change lock out anyone already holding a token.
    """
    return create_access_token(
        {
            "sub": str(user.id),
            "role": user.role,
            "tv": user.token_version,
        }
    )