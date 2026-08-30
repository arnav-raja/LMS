"""Rate limiting for sign-in.

Without this, `/auth/login` will answer as fast as bcrypt allows, forever.
There is no self-service registration here, so usernames are predictable
from the company directory — guessing passwords against a known name is
the realistic attack on this application, not anything more exotic.

The limit is per identifier rather than per IP. An attacker can trivially
change IP; they cannot change which account they are trying to get into.
The trade-off is that someone else's guessing can lock a real user out of
signing in for the window, which is why the window is short.
"""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.errors import TooManyAttemptsError

from app.models.login_attempt import LoginAttempt

from app.utils.time import utc_now


MAX_FAILURES = 5
WINDOW = timedelta(minutes=15)


def _window_start():
    return utc_now() - WINDOW


def check_not_locked_out(db: Session, identifier: str) -> None:
    """Raise if this identifier has failed too often too recently.

    Called before the password is checked, so a locked-out caller does
    not even get the timing signal of a bcrypt comparison.
    """
    failures = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.identifier == identifier,
            LoginAttempt.succeeded == False,
            LoginAttempt.attempted_at >= _window_start(),
        )
        .count()
    )

    if failures >= MAX_FAILURES:
        raise TooManyAttemptsError(
            "Too many failed sign-in attempts. Wait a few minutes and "
            "try again."
        )


def record_attempt(db: Session, identifier: str, succeeded: bool) -> None:
    """Record the outcome, and tidy up.

    A successful sign-in clears that identifier's failures, so someone who
    mistypes four times and then gets it right is not left one slip away
    from a lockout.
    """
    db.add(
        LoginAttempt(
            identifier=identifier,
            succeeded=succeeded,
            attempted_at=utc_now(),
        )
    )

    if succeeded:
        (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.identifier == identifier,
                LoginAttempt.succeeded == False,
            )
            .delete(synchronize_session=False)
        )

    # Anything older than the window can never affect a decision again.
    # Pruning here keeps the table from growing without a scheduled job.
    (
        db.query(LoginAttempt)
        .filter(LoginAttempt.attempted_at < _window_start())
        .delete(synchronize_session=False)
    )

    db.commit()
