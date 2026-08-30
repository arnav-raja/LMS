"""Sign-in rate limiting, password rules, and token revocation."""

import pytest

from app.services import login_guard
from app.services.password_policy import MINIMUM_LENGTH
from app.services.password_policy import validate_password
from app.errors import InvalidInputError


# --------------------------------------------------------- rate limiting --

def fail_login(client, identifier, times=1):
    for _ in range(times):
        response = client.post(
            "/auth/login",
            data={"username": identifier, "password": "wrong-password"},
        )
    return response


def test_repeated_failures_lock_the_identifier_out(client, student, password):
    fail_login(client, student.username, times=login_guard.MAX_FAILURES)

    blocked = client.post(
        "/auth/login",
        data={"username": student.username, "password": password},
    )

    assert blocked.status_code == 429
    assert "Too many failed sign-in attempts" in blocked.json()["detail"]


def test_the_correct_password_is_refused_while_locked_out(
    client, student, password
):
    """The lockout has to hold even for the real password, or it stops an
    attacker only until they guess right."""
    fail_login(client, student.username, times=login_guard.MAX_FAILURES)

    assert (
        client.post(
            "/auth/login",
            data={"username": student.username, "password": password},
        ).status_code
        == 429
    )


def test_attempts_below_the_limit_do_not_lock_out(client, student, password):
    fail_login(client, student.username, times=login_guard.MAX_FAILURES - 1)

    response = client.post(
        "/auth/login",
        data={"username": student.username, "password": password},
    )

    assert response.status_code == 200


def test_a_success_clears_the_failure_count(client, student, password):
    """Four fumbles then a correct password should not leave someone one
    slip from a lockout."""
    fail_login(client, student.username, times=login_guard.MAX_FAILURES - 1)

    assert (
        client.post(
            "/auth/login",
            data={"username": student.username, "password": password},
        ).status_code
        == 200
    )

    fail_login(client, student.username, times=login_guard.MAX_FAILURES - 1)

    assert (
        client.post(
            "/auth/login",
            data={"username": student.username, "password": password},
        ).status_code
        == 200
    )


def test_the_lockout_is_per_identifier(client, student, other_student, password):
    """One account being attacked must not lock everyone else out."""
    fail_login(client, student.username, times=login_guard.MAX_FAILURES)

    response = client.post(
        "/auth/login",
        data={"username": other_student.username, "password": password},
    )

    assert response.status_code == 200


def test_unknown_identifiers_are_rate_limited_too(client):
    """Guessing usernames is the first half of the attack, so it counts."""
    fail_login(client, "does-not-exist", times=login_guard.MAX_FAILURES)

    response = client.post(
        "/auth/login",
        data={"username": "does-not-exist", "password": "anything"},
    )

    assert response.status_code == 429


# ------------------------------------------------------- password policy --

@pytest.mark.parametrize(
    "password",
    [
        "",
        "   ",
        "short",
        "password123",
        "Welcome123",
        "aaaaaaaaaaaa",
        "ababababab",
    ],
)
def test_weak_passwords_are_refused(password):
    with pytest.raises(InvalidInputError):
        validate_password(password)


@pytest.mark.parametrize(
    "password",
    [
        "correct-horse-battery",
        "a reasonable phrase",
        "Tr0ub4dor&3xtra",
    ],
)
def test_reasonable_passwords_are_accepted(password):
    validate_password(password)


def test_creating_a_user_with_a_weak_password_is_refused(
    client, admin_headers
):
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={
            "name": "Weak",
            "username": "weak",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "too easy to guess" in response.json()["detail"]


def test_a_short_password_says_how_long_it_must_be(client, admin_headers):
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={"name": "Short", "username": "short", "password": "abc123"},
    )

    assert response.status_code == 400
    assert str(MINIMUM_LENGTH) in response.json()["detail"]


def test_a_weak_password_on_edit_changes_nothing_else(
    client, admin_headers, student
):
    """The password is checked before anything is written, so a rejected
    edit must not have applied the name change alongside it."""
    response = client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Should Not Stick", "password": "short"},
    )

    assert response.status_code == 400

    after = client.get("/admin/users", headers=admin_headers).json()
    names = [user["name"] for user in after]
    assert "Should Not Stick" not in names


def test_an_account_can_still_be_edited_without_touching_the_password(
    client, admin_headers, student
):
    response = client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Ada Byron"},
    )

    assert response.status_code == 200


# ----------------------------------------------------- token revocation --

def test_changing_a_password_invalidates_existing_tokens(
    client, admin_headers, student, student_headers
):
    """Resetting a compromised account's password has to lock the
    intruder out now, not up to eight hours later when their token
    happens to expire."""
    assert client.get("/auth/me", headers=student_headers).status_code == 200

    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"password": "a-brand-new-passphrase"},
    )

    assert client.get("/auth/me", headers=student_headers).status_code == 401


def test_the_new_password_issues_a_working_token(
    client, admin_headers, student
):
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"password": "a-brand-new-passphrase"},
    )

    token = client.post(
        "/auth/login",
        data={
            "username": student.username,
            "password": "a-brand-new-passphrase",
        },
    ).json()["access_token"]

    assert (
        client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 200
    )


def test_changing_a_role_invalidates_existing_tokens(
    client, admin_headers, student, student_headers
):
    """Demoting an admin should end their session, not leave them holding
    a token that still passes every check."""
    assert client.get("/auth/me", headers=student_headers).status_code == 200

    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"role": "admin"},
    )

    assert client.get("/auth/me", headers=student_headers).status_code == 401


def test_an_unrelated_edit_leaves_the_session_alone(
    client, admin_headers, student, student_headers
):
    """Correcting somebody's name should not sign them out."""
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Ada Byron"},
    )

    assert client.get("/auth/me", headers=student_headers).status_code == 200


def test_a_token_with_no_version_claim_is_rejected(client, student):
    """Tokens minted before this claim existed must not keep working."""
    from app.services.jwt_service import create_access_token

    legacy = create_access_token({"sub": str(student.id), "role": student.role})

    assert (
        client.get(
            "/auth/me", headers={"Authorization": f"Bearer {legacy}"}
        ).status_code
        == 401
    )


def test_a_token_with_a_nonsense_subject_is_rejected(client):
    """`sub` used to be passed straight to int(), which raised and
    surfaced as a 500 rather than a 401."""
    from app.services.jwt_service import create_access_token

    forged = create_access_token({"sub": "not-a-number", "tv": 1})

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {forged}"}
    )

    assert response.status_code == 401
