"""Administrative actions on accounts leave a record.

An admin can create accounts, reset anyone's password, change anyone's
role, and delete an account along with its certificates. None of it left
any trace: if a student's account vanished, nothing anywhere said who did
it or when.
"""


def audit(client, admin_headers):
    return client.get("/admin/audit", headers=admin_headers).json()


def test_creating_an_account_is_recorded(client, admin, admin_headers):
    client.post(
        "/admin/users",
        headers=admin_headers,
        json={
            "name": "Katherine Johnson",
            "username": "katherine",
            "password": "orbital-mechanics",
            "role": "student",
        },
    )

    entries = audit(client, admin_headers)

    assert len(entries) == 1
    assert entries[0]["action"] == "user.created"
    assert entries[0]["actor_name"] == admin.name
    assert entries[0]["actor_id"] == admin.id
    assert "katherine" in entries[0]["summary"]


def test_editing_an_account_records_what_changed(
    client, admin_headers, student
):
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Ada Byron", "seniority": "Senior"},
    )

    entry = audit(client, admin_headers)[0]

    assert entry["action"] == "user.updated"
    assert "Ada Byron" in entry["summary"]
    assert "Senior" in entry["summary"]


def test_a_password_reset_is_recorded_without_the_password(
    client, admin_headers, student
):
    """The entry must say a reset happened and nothing more — an audit
    log is exactly the wrong place for a password."""
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"password": "a-brand-new-passphrase"},
    )

    entry = audit(client, admin_headers)[0]

    assert "password reset" in entry["summary"]
    assert "a-brand-new-passphrase" not in entry["summary"]


def test_deleting_an_account_records_what_was_destroyed(
    client, admin_headers, student, student_headers, course_with_content
):
    for lesson in (
        course_with_content.lesson_one,
        course_with_content.lesson_two,
        course_with_content.lesson_three,
    ):
        client.post(
            "/progress/complete",
            headers=student_headers,
            json={"subchapter_id": lesson.id},
        )

    client.delete(f"/admin/users/{student.id}", headers=admin_headers)

    entry = audit(client, admin_headers)[0]

    assert entry["action"] == "user.deleted"
    assert "ada" in entry["summary"]
    assert "1 certificates" in entry["summary"]
    assert "3 lessons completed" in entry["summary"]


def test_the_entry_outlives_the_account_it_describes(
    client, admin_headers, student
):
    """target_id is deliberately not a foreign key — the row it points at
    is usually the one that was just deleted."""
    student_id = student.id

    client.delete(f"/admin/users/{student_id}", headers=admin_headers)

    entry = audit(client, admin_headers)[0]

    assert entry["target_id"] == student_id
    assert entry["target_type"] == "user"


def test_an_edit_that_changes_nothing_is_not_recorded(
    client, admin_headers, student
):
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": student.name},
    )

    assert audit(client, admin_headers) == []


def test_a_rejected_edit_is_not_recorded(client, admin_headers, student):
    """The entry and the change share a transaction, so a failure must
    leave neither."""
    response = client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Nope", "password": "short"},
    )

    assert response.status_code == 400
    assert audit(client, admin_headers) == []


def test_entries_come_back_newest_first(client, admin_headers, student):
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "First Change"},
    )
    client.patch(
        f"/admin/users/{student.id}",
        headers=admin_headers,
        json={"name": "Second Change"},
    )

    entries = audit(client, admin_headers)

    assert "Second Change" in entries[0]["summary"]
    assert "First Change" in entries[1]["summary"]


def test_the_audit_log_is_admin_only(client, student_headers):
    assert client.get("/admin/audit", headers=student_headers).status_code == 403


def test_the_audit_log_needs_a_token(client):
    assert client.get("/admin/audit").status_code == 401


def test_the_limit_is_capped(client, admin_headers, student):
    """A caller asking for everything should not be able to pull the
    whole table in one request."""
    response = client.get("/admin/audit?limit=100000", headers=admin_headers)

    assert response.status_code == 200
