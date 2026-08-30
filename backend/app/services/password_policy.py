"""What counts as an acceptable password.

Every account here is created by an administrator on someone else's
behalf, which makes weak passwords more likely than usual: whoever is
typing it is not the person who has to live with it, and "Welcome123" is
quick. These rules are deliberately modest — long enough to matter, with
no character-class gymnastics, which push people towards `Passw0rd!` and
buy very little.

Applied when a password is set or changed, never to one already stored:
existing accounts are not locked out by a rule that arrived after them.
They will be checked the next time their password is changed.
"""

from app.errors import InvalidInputError


MINIMUM_LENGTH = 10

# Not an attempt at a breach corpus — just the handful that show up when
# someone is setting a password for another person and wants to move on.
OBVIOUS_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "passw0rd",
    "welcome1",
    "welcome123",
    "changeme",
    "changeme123",
    "letmein123",
    "qwerty123",
    "1234567890",
    "12345678901",
    "admin12345",
    "administrator",
}


def validate_password(password: str) -> None:
    """Raise InvalidInputError if this password may not be used.

    The messages say what to do rather than what went wrong, because the
    person reading them is usually an admin creating an account and needs
    to get past it, not a lecture.
    """
    if password is None or not password.strip():
        raise InvalidInputError("A password is required.")

    if len(password) < MINIMUM_LENGTH:
        raise InvalidInputError(
            f"Password must be at least {MINIMUM_LENGTH} characters. "
            "A short phrase works well."
        )

    if password.lower() in OBVIOUS_PASSWORDS:
        raise InvalidInputError(
            "That password is too easy to guess. Try a short phrase "
            "instead."
        )

    if len(set(password)) < 4:
        raise InvalidInputError(
            "That password repeats too few characters. Try a short "
            "phrase instead."
        )
