"""Course listing, publish/archive, the admin course builder, and the
department/seniority access rules that decide who sees what."""


# ------------------------------------------------------------- listing ----

def test_admin_sees_every_course_including_drafts(
    client, admin_headers, make_course
):
    make_course(title="Published One", status="published")
    make_course(title="Draft One", status="draft")

    response = client.get("/courses", headers=admin_headers)

    assert response.status_code == 200
    titles = [course["title"] for course in response.json()]
    assert "Published One" in titles
    assert "Draft One" in titles


def test_student_sees_only_granted_published_courses(
    client, student_headers, make_course, grant_access
):
    granted = make_course(title="Granted", status="published")
    grant_access(granted)

    ungranted = make_course(title="Ungranted", status="published")

    draft = make_course(title="Granted But Draft", status="draft")
    grant_access(draft)

    response = client.get("/courses", headers=student_headers)

    assert response.status_code == 200
    titles = [course["title"] for course in response.json()]
    assert titles == ["Granted"]
    assert ungranted.title not in titles
    assert draft.title not in titles


def test_student_with_no_profile_sees_nothing(
    client, make_user, headers_for, make_course, grant_access
):
    course = make_course()
    grant_access(course)

    no_profile = make_user(
        name="Unassigned",
        username="unassigned",
        email="unassigned@example.com",
        department=None,
        seniority=None,
    )

    response = client.get("/courses", headers=headers_for(no_profile))

    assert response.status_code == 200
    assert response.json() == []


def test_listing_courses_requires_a_token(client):
    assert client.get("/courses").status_code == 401


# ------------------------------------------------- publish and archive ----

def test_admin_can_publish_a_draft(client, admin_headers, make_course):
    course = make_course(status="draft")

    response = client.post(
        f"/courses/{course.id}/publish",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"


def test_admin_can_archive_a_course(client, admin_headers, make_course):
    course = make_course(status="published")

    response = client.post(
        f"/courses/{course.id}/archive",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"


def test_archiving_hides_a_course_from_students(
    client, admin_headers, student_headers, make_course, grant_access
):
    course = make_course(title="Soon Archived", status="published")
    grant_access(course)

    assert len(client.get("/courses", headers=student_headers).json()) == 1

    client.post(f"/courses/{course.id}/archive", headers=admin_headers)

    assert client.get("/courses", headers=student_headers).json() == []


def test_publish_not_found(client, admin_headers):
    assert (
        client.post("/courses/999999/publish", headers=admin_headers).status_code
        == 404
    )


def test_archive_not_found(client, admin_headers):
    assert (
        client.post("/courses/999999/archive", headers=admin_headers).status_code
        == 404
    )


def test_publish_forbidden_for_student(client, student_headers, make_course):
    course = make_course(status="draft")

    response = client.post(
        f"/courses/{course.id}/publish",
        headers=student_headers,
    )

    assert response.status_code == 403


# ------------------------------------------------------------- builder ----

COURSE_PAYLOAD = {
    "title": "Fire Safety",
    "description": "What to do when the alarm sounds",
    "status": "published",
    "chapters": [
        {
            "title": "Before The Alarm",
            "description": "Preparation",
            "subchapters": [
                {"title": "Know Your Exits", "content": "Exit content"},
                {"title": "Assembly Points", "content": "Assembly content"},
            ],
        },
        {
            "title": "After The Alarm",
            "description": "Response",
            "subchapters": [
                {"title": "Stay Calm", "content": "Calm content"},
            ],
        },
    ],
}


def test_create_course_builds_the_whole_tree(client, admin_headers):
    response = client.post(
        "/admin/courses",
        headers=admin_headers,
        json=COURSE_PAYLOAD,
    )

    assert response.status_code == 200
    course = response.json()
    assert course["title"] == "Fire Safety"
    assert course["num_chapters"] == 2

    chapters = client.get(
        f"/courses/{course['id']}/chapters",
        headers=admin_headers,
    ).json()

    assert [chapter["title"] for chapter in chapters] == [
        "Before The Alarm",
        "After The Alarm",
    ]
    assert len(chapters[0]["subchapters"]) == 2
    assert len(chapters[1]["subchapters"]) == 1


def test_create_course_forbidden_for_student(client, student_headers):
    response = client.post(
        "/admin/courses",
        headers=student_headers,
        json=COURSE_PAYLOAD,
    )

    assert response.status_code == 403


def test_update_course_edits_in_place(client, admin_headers):
    created = client.post(
        "/admin/courses",
        headers=admin_headers,
        json=COURSE_PAYLOAD,
    ).json()

    edited = dict(COURSE_PAYLOAD, title="Fire Safety (Revised)")

    response = client.put(
        f"/admin/courses/{created['id']}",
        headers=admin_headers,
        json=edited,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Fire Safety (Revised)"
    assert response.json()["id"] == created["id"]


def test_update_course_not_found(client, admin_headers):
    response = client.put(
        "/admin/courses/999999",
        headers=admin_headers,
        json=COURSE_PAYLOAD,
    )

    assert response.status_code == 404


def test_update_course_forbidden_for_student(client, student_headers, make_course):
    course = make_course()

    response = client.put(
        f"/admin/courses/{course.id}",
        headers=student_headers,
        json=COURSE_PAYLOAD,
    )

    assert response.status_code == 403


def test_delete_course_removes_it(client, admin_headers, make_course):
    course = make_course(title="Temporary")

    response = client.delete(
        f"/admin/courses/{course.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    remaining = client.get("/courses", headers=admin_headers).json()
    assert "Temporary" not in [item["title"] for item in remaining]


def test_delete_course_not_found(client, admin_headers):
    assert (
        client.delete("/admin/courses/999999", headers=admin_headers).status_code
        == 404
    )


def test_delete_course_forbidden_for_student(client, student_headers, make_course):
    course = make_course()

    response = client.delete(
        f"/admin/courses/{course.id}",
        headers=student_headers,
    )

    assert response.status_code == 403


# -------------------------------------------------------------- access ----

def test_grant_access_makes_a_course_visible(
    client, admin_headers, student_headers, make_course
):
    course = make_course(title="Newly Granted", status="published")

    assert client.get("/courses", headers=student_headers).json() == []

    response = client.post(
        f"/admin/courses/{course.id}/access",
        headers=admin_headers,
        json={"department": "EC", "seniority": "Mid"},
    )

    assert response.status_code == 200

    visible = client.get("/courses", headers=student_headers).json()
    assert [item["title"] for item in visible] == ["Newly Granted"]


def test_granting_the_same_rule_twice_is_harmless(
    client, admin_headers, make_course
):
    course = make_course()
    payload = {"department": "EC", "seniority": "Mid"}

    first = client.post(
        f"/admin/courses/{course.id}/access", headers=admin_headers, json=payload
    )
    second = client.post(
        f"/admin/courses/{course.id}/access", headers=admin_headers, json=payload
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    rules = client.get(
        f"/admin/courses/{course.id}/access", headers=admin_headers
    ).json()
    assert len(rules) == 1


def test_revoke_access_hides_the_course_again(
    client, admin_headers, student_headers, make_course, grant_access
):
    course = make_course()
    grant_access(course)

    assert len(client.get("/courses", headers=student_headers).json()) == 1

    response = client.request(
        "DELETE",
        f"/admin/courses/{course.id}/access",
        headers=admin_headers,
        json={"department": "EC", "seniority": "Mid"},
    )

    assert response.status_code == 200
    assert client.get("/courses", headers=student_headers).json() == []


def test_revoke_access_not_found(client, admin_headers, make_course):
    course = make_course()

    response = client.request(
        "DELETE",
        f"/admin/courses/{course.id}/access",
        headers=admin_headers,
        json={"department": "HR", "seniority": "Manager"},
    )

    assert response.status_code == 404


def test_access_routes_404_on_unknown_course(client, admin_headers):
    assert (
        client.get("/admin/courses/999999/access", headers=admin_headers).status_code
        == 404
    )
    assert (
        client.post(
            "/admin/courses/999999/access",
            headers=admin_headers,
            json={"department": "EC", "seniority": "Mid"},
        ).status_code
        == 404
    )


def test_access_routes_forbidden_for_student(client, student_headers, make_course):
    course = make_course()

    assert (
        client.get(
            f"/admin/courses/{course.id}/access", headers=student_headers
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/admin/courses/{course.id}/access",
            headers=student_headers,
            json={"department": "EC", "seniority": "Mid"},
        ).status_code
        == 403
    )


def test_grant_access_rejects_an_unknown_department(
    client, admin_headers, make_course
):
    course = make_course()

    response = client.post(
        f"/admin/courses/{course.id}/access",
        headers=admin_headers,
        json={"department": "NOPE", "seniority": "Mid"},
    )

    assert response.status_code == 422
