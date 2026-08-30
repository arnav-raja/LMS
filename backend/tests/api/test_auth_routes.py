"""Login and identity routes."""


def test_login_with_username(client, student, password):
    response = client.post(
        "/auth/login",
        data={"username": student.username, "password": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_email(client, student, password):
    """The form field is called `username`, but an email works in it too."""
    response = client.post(
        "/auth/login",
        data={"username": student.email, "password": password},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password(client, student):
    response = client.post(
        "/auth/login",
        data={"username": student.username, "password": "not-the-password"},
    )

    assert response.status_code == 401


def test_login_with_unknown_user(client, password):
    response = client.post(
        "/auth/login",
        data={"username": "nobody", "password": password},
    )

    assert response.status_code == 401


def test_login_error_does_not_reveal_which_half_was_wrong(client, student, password):
    unknown = client.post(
        "/auth/login",
        data={"username": "nobody", "password": password},
    )
    wrong_password = client.post(
        "/auth/login",
        data={"username": student.username, "password": "not-the-password"},
    )

    assert unknown.json()["detail"] == wrong_password.json()["detail"]


def test_token_from_login_works_on_a_protected_route(client, student, password):
    token = client.post(
        "/auth/login",
        data={"username": student.username, "password": password},
    ).json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == student.id


def test_me_returns_the_signed_in_user(client, student, student_headers):
    response = client.get("/auth/me", headers=student_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == student.id
    assert body["name"] == student.name
    assert "password_hash" not in body


def test_me_without_a_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_a_malformed_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_public_routes_need_no_token(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json() == {"status": "running"}
