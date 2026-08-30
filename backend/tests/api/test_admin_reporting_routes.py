"""Admin dashboard, reference-data lookups, and the two progress reports."""


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


# ----------------------------------------------------------- dashboard ----

def test_admin_dashboard_counts(client, admin_headers, student, make_course):
    make_course(title="Live", status="published")
    make_course(title="In Progress", status="draft")

    response = client.get("/admin/dashboard", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_students"] == 1
    assert body["published_courses"] == 1
    assert body["draft_courses"] == 1


def test_admin_dashboard_forbidden_for_student(client, student_headers):
    assert client.get("/admin/dashboard", headers=student_headers).status_code == 403


def test_admin_dashboard_requires_a_token(client):
    assert client.get("/admin/dashboard").status_code == 401


# ------------------------------------------------------ reference data ----

def test_departments_are_available_to_any_signed_in_user(
    client, student_headers
):
    """Not an admin action despite the URL — every user needs these to
    render their own department in the sidebar."""
    response = client.get("/admin/departments", headers=student_headers)

    assert response.status_code == 200
    departments = response.json()
    assert len(departments) == 9
    assert {"code": "EC", "label": "E-Commerce"} in departments


def test_roles_are_available_to_any_signed_in_user(client, student_headers):
    response = client.get("/admin/roles", headers=student_headers)

    assert response.status_code == 200
    assert [row["value"] for row in response.json()] == [
        "Manager",
        "Senior",
        "Mid",
        "Junior",
    ]


def test_reference_data_still_requires_a_token(client):
    assert client.get("/admin/departments").status_code == 401
    assert client.get("/admin/roles").status_code == 401


# -------------------------------------------------------------- students --

def test_student_list_excludes_admins(client, admin_headers, admin, student):
    response = client.get("/admin/students", headers=admin_headers)

    assert response.status_code == 200
    names = [row["name"] for row in response.json()]
    assert student.name in names
    assert admin.name not in names


def test_student_list_forbidden_for_student(client, student_headers):
    assert client.get("/admin/students", headers=student_headers).status_code == 403


def test_student_progress_detail(
    client, admin_headers, student, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.get(
        f"/admin/students/{student.id}/progress",
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == student.name
    assert body["department"] == "EC"
    assert len(body["courses"]) == 1

    course = body["courses"][0]
    assert course["percentage"] == 33.33
    assert len(course["chapters"]) == 2
    assert course["chapters"][0]["subchapters"][0]["is_completed"] is True
    assert course["chapters"][0]["subchapters"][1]["is_completed"] is False


def test_student_progress_detail_not_found(client, admin_headers):
    assert (
        client.get(
            "/admin/students/999999/progress", headers=admin_headers
        ).status_code
        == 404
    )


def test_student_progress_detail_forbidden_for_student(
    client, student_headers, other_student
):
    assert (
        client.get(
            f"/admin/students/{other_student.id}/progress",
            headers=student_headers,
        ).status_code
        == 403
    )


# ---------------------------------------------------------------- roster --

def test_course_roster_lists_students_the_rules_reach(
    client, admin_headers, student, student_headers, other_student,
    course_with_content
):
    """The roster is derived from the access rules, not from an enrolment
    table — a student in a different department must not appear."""
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.get(
        f"/admin/courses/{course_with_content.course.id}/students",
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["course_title"] == "Security Basics"

    names = [row["name"] for row in body["students"]]
    assert student.name in names
    assert other_student.name not in names

    row = next(r for r in body["students"] if r["name"] == student.name)
    assert row["completed_subchapters"] == 1
    assert row["total_subchapters"] == 3
    assert row["percentage"] == 33.33
    assert row["last_activity"] is not None


def test_course_roster_is_empty_without_access_rules(
    client, admin_headers, make_course
):
    course = make_course(title="Nobody Can See This")

    body = client.get(
        f"/admin/courses/{course.id}/students",
        headers=admin_headers,
    ).json()

    assert body["students"] == []


def test_course_roster_not_found(client, admin_headers):
    assert (
        client.get(
            "/admin/courses/999999/students", headers=admin_headers
        ).status_code
        == 404
    )


def test_course_roster_forbidden_for_student(
    client, student_headers, course_with_content
):
    assert (
        client.get(
            f"/admin/courses/{course_with_content.course.id}/students",
            headers=student_headers,
        ).status_code
        == 403
    )
