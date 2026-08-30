"""Marking lessons complete, the sequential unlock rule, and the two
progress summaries built on top of them."""


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


def test_complete_the_first_lesson(client, student_headers, course_with_content):
    response = complete(
        client, student_headers, course_with_content.lesson_one.id
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_completed"] is True
    assert body["certificate_issued"] is False


def test_completing_a_lesson_unlocks_the_next_one(
    client, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    chapters = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=student_headers,
    ).json()

    lessons = chapters[0]["subchapters"]
    assert lessons[1]["is_locked"] is False
    assert lessons[1]["content"] == "Body text"


def test_cannot_skip_ahead_to_a_locked_lesson(
    client, student_headers, course_with_content
):
    response = complete(
        client, student_headers, course_with_content.lesson_two.id
    )

    assert response.status_code == 403
    assert "previous subchapter" in response.json()["detail"]


def test_completing_a_lesson_twice_is_harmless(
    client, student_headers, course_with_content
):
    first = complete(client, student_headers, course_with_content.lesson_one.id)
    second = complete(client, student_headers, course_with_content.lesson_one.id)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_complete_unknown_subchapter(client, student_headers):
    response = complete(client, student_headers, 999999)

    assert response.status_code == 404


def test_complete_forbidden_without_course_access(
    client, other_student, headers_for, course_with_content
):
    response = complete(
        client, headers_for(other_student), course_with_content.lesson_one.id
    )

    assert response.status_code == 403


def test_complete_requires_a_token(client, course_with_content):
    response = client.post(
        "/progress/complete",
        json={"subchapter_id": course_with_content.lesson_one.id},
    )

    assert response.status_code == 401


def test_my_progress_lists_completed_lessons(
    client, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.get("/progress/me", headers=student_headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["subchapter_id"] == course_with_content.lesson_one.id


def test_my_progress_requires_a_token(client):
    assert client.get("/progress/me").status_code == 401


# ------------------------------------------------------------ learning ----

def test_continue_points_at_the_first_unfinished_lesson(
    client, student_headers, course_with_content
):
    response = client.get(
        f"/learning/courses/{course_with_content.course.id}/continue",
        headers=student_headers,
    )

    assert response.status_code == 200
    assert response.json()["subchapter_id"] == course_with_content.lesson_one.id


def test_continue_advances_as_lessons_are_completed(
    client, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.get(
        f"/learning/courses/{course_with_content.course.id}/continue",
        headers=student_headers,
    )

    assert response.json()["subchapter_id"] == course_with_content.lesson_two.id


def test_continue_returns_404_once_everything_is_done(
    client, student_headers, course_with_content
):
    """The frontend treats this 404 as "course finished", not as an error."""
    for lesson in (
        course_with_content.lesson_one,
        course_with_content.lesson_two,
        course_with_content.lesson_three,
    ):
        complete(client, student_headers, lesson.id)

    response = client.get(
        f"/learning/courses/{course_with_content.course.id}/continue",
        headers=student_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Course completed"


def test_continue_forbidden_without_access(
    client, other_student, headers_for, course_with_content
):
    response = client.get(
        f"/learning/courses/{course_with_content.course.id}/continue",
        headers=headers_for(other_student),
    )

    assert response.status_code == 403


def test_course_progress_counts_lessons_and_chapters(
    client, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.get(
        f"/learning/courses/{course_with_content.course.id}/progress",
        headers=student_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_subchapters"] == 3
    assert body["completed_subchapters"] == 1
    assert body["total_chapters"] == 2
    assert body["completed_chapters"] == 0
    assert body["percentage"] == 33.33


def test_course_progress_reaches_one_hundred(
    client, student_headers, course_with_content
):
    for lesson in (
        course_with_content.lesson_one,
        course_with_content.lesson_two,
        course_with_content.lesson_three,
    ):
        complete(client, student_headers, lesson.id)

    body = client.get(
        f"/learning/courses/{course_with_content.course.id}/progress",
        headers=student_headers,
    ).json()

    assert body["percentage"] == 100
    assert body["completed_chapters"] == 2


def test_course_progress_forbidden_without_access(
    client, other_student, headers_for, course_with_content
):
    response = client.get(
        f"/learning/courses/{course_with_content.course.id}/progress",
        headers=headers_for(other_student),
    )

    assert response.status_code == 403


# ----------------------------------------------------- student dashboard ---

def test_my_dashboard_summarises_each_course(
    client, student, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.get("/me/dashboard", headers=student_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == student.id
    assert len(body["courses"]) == 1

    course = body["courses"][0]
    assert course["progress"] == 33.33
    assert course["next_subchapter"] == "Lesson Two"


def test_my_dashboard_requires_a_token(client):
    assert client.get("/me/dashboard").status_code == 401
