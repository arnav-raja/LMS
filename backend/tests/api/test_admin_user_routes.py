"""Routes for creating, editing and deleting accounts.

Accounts can only be made by an admin through these routes — there is no
self-service registration — so a break here locks everyone out of the
product. Both the create and the edit route were passing the wrong
arguments to their service and returning 500 on every call; the service
unit tests passed throughout, because they call the service directly.
"""

def test_create_user_succeeds(client, admin_headers):
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={
            "name": "Katherine Johnson",
            "username": "katherine",
            "email": "katherine@example.com",
            "password": "orbital-mechanics",
            "role": "student",
            "department": "EC",
            "seniority": "Senior",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "katherine"
    assert body["department"] == "EC"
    assert body["seniority"] == "Senior"
    assert "password" not in body
    assert "password_hash" not in body


def test_create_user_allows_omitting_optional_profile(client, admin_headers):
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={
            "name": "No Profile",
            "username": "noprofile",
            "password": "some-password",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] is None
    assert body["department"] is None
    assert body["seniority"] is None
    assert body["role"] == "student"


def test_create_user_rejects_duplicate_username(client, admin_headers, student):
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={
            "name": "Impostor",
            "username": student.username,
            "password": "another-password",
        },
    )

    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


def test_create_user_rejects_duplicate_email(client, admin_headers, student):
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={
            "name": "Impostor",
            "username": "impostor",
            "email": student.email,
            "password": "another-password",
        },
    )

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_create_user_rejects_unknown_department(client, admin_headers):
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={
            "name": "Bad Department",
            "username": "baddept",
            "password": "another-password",
            "department": "NOPE",
        },
    )

    assert response.status_code == 422


def test_create_user_forbidden_for_student(client, student_headers):
    response = client.post(
        "/admin/users",
        headers=student_headers,
        json={
            "name": "Sneaky",
            "username": "sneaky",
            "password": "another-password",
        },
    )

    assert response.status_code == 403


def test_create_user_requires_a_token(client):
    response = client.post(
        "/admin/users",
        json={"name": "X", "username": "x", "password": "y"},
    )

    assert response.status_code == 401


# ------------------------------------------------------------------ edit ---

def test_update_user_succeeds(client, admin_headers, student):
    response = client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Ada Byron"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Ada Byron"


def test_update_user_leaves_omitted_fields_alone(client, admin_headers, student):
    """The distinction the `provided_fields` argument exists to make: a
    field left out of the PATCH keeps its value."""
    response = client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Ada Byron"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["department"] == "EC"
    assert body["seniority"] == "Mid"


def test_update_user_can_clear_fields_sent_as_null(client, admin_headers, student):
    """The other half of that distinction: a field explicitly sent as null
    is genuinely cleared."""
    response = client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"email": None, "department": None, "seniority": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] is None
    assert body["department"] is None
    assert body["seniority"] is None


def test_update_user_rejects_duplicate_username(
    client, admin_headers, student, other_student
):
    response = client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"username": other_student.username},
    )

    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


def test_update_user_not_found(client, admin_headers):
    response = client.patch(
        "/admin/users/999999",
        headers=admin_headers,
        json={"name": "Ghost"},
    )

    assert response.status_code == 404


def test_update_user_forbidden_for_student(client, student_headers, other_student):
    response = client.patch(
        f"/admin/users/{other_student.id}",
        headers=student_headers,
        json={"name": "Hijacked"},
    )

    assert response.status_code == 403


def test_update_user_changes_the_working_password(client, admin_headers, student):
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"password": "brand-new-password"},
    )

    response = client.post(
        "/auth/login",
        data={"username": student.username, "password": "brand-new-password"},
    )

    assert response.status_code == 200


# ---------------------------------------------------------------- delete ---

def test_delete_user_succeeds(client, admin_headers, student):
    response = client.delete(
        f"/admin/users/{student.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    gone = client.get("/admin/users", headers=admin_headers).json()
    assert student.username not in [user["username"] for user in gone]


def test_delete_user_rejects_deleting_yourself(client, admin, admin_headers):
    response = client.delete(
        f"/admin/users/{admin.id}",
        headers=admin_headers,
    )

    assert response.status_code == 400
    assert "your own account" in response.json()["detail"]


def test_delete_user_not_found(client, admin_headers):
    response = client.delete("/admin/users/999999", headers=admin_headers)

    assert response.status_code == 404


def test_delete_user_forbidden_for_student(client, student_headers, other_student):
    response = client.delete(
        f"/admin/users/{other_student.id}",
        headers=student_headers,
    )

    assert response.status_code == 403


def test_deleted_user_can_no_longer_authenticate(
    client, admin_headers, student, headers_for
):
    headers = headers_for(student)
    assert client.get("/auth/me", headers=headers).status_code == 200

    client.delete(f"/admin/users/{student.id}", headers=admin_headers)

    assert client.get("/auth/me", headers=headers).status_code == 401


# ------------------------------------------------------------------ list ---

def test_list_users_returns_everyone(client, admin_headers, admin, student):
    response = client.get("/admin/users", headers=admin_headers)

    assert response.status_code == 200
    usernames = [user["username"] for user in response.json()]
    assert admin.username in usernames
    assert student.username in usernames


def test_list_users_forbidden_for_student(client, student_headers):
    assert client.get("/admin/users", headers=student_headers).status_code == 403
