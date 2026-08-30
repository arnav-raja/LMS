"""Chapter reading routes, including the rule that a locked lesson must
not hand its content to the browser."""


def test_list_chapters_for_a_student_with_access(
    client, student_headers, course_with_content
):
    response = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=student_headers,
    )

    assert response.status_code == 200
    chapters = response.json()
    assert [chapter["title"] for chapter in chapters] == [
        "Chapter One",
        "Chapter Two",
    ]


def test_list_chapters_forbidden_without_access(
    client, other_student, headers_for, course_with_content
):
    response = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=headers_for(other_student),
    )

    assert response.status_code == 403


def test_first_lesson_is_unlocked_and_the_rest_are_not(
    client, student_headers, course_with_content
):
    chapters = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=student_headers,
    ).json()

    lessons = chapters[0]["subchapters"]
    assert lessons[0]["is_locked"] is False
    assert lessons[1]["is_locked"] is True


def test_locked_lesson_content_is_withheld_from_the_response(
    client, student_headers, course_with_content
):
    """The lock has to be enforced on the server. If the body were sent and
    merely hidden by the UI, anyone could read ahead from the network tab."""
    chapters = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=student_headers,
    ).json()

    lessons = chapters[0]["subchapters"]
    assert lessons[0]["content"] == "Body text"
    assert lessons[1]["content"] is None


def test_admin_sees_every_lesson_unlocked(
    client, admin_headers, course_with_content
):
    chapters = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=admin_headers,
    ).json()

    for chapter in chapters:
        for lesson in chapter["subchapters"]:
            assert lesson["is_locked"] is False
            assert lesson["content"] == "Body text"


def test_get_one_chapter(client, student_headers, course_with_content):
    response = client.get(
        f"/courses/{course_with_content.course.id}"
        f"/chapters/{course_with_content.chapter_one.id}",
        headers=student_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Chapter One"


def test_get_one_chapter_not_found(client, student_headers, course_with_content):
    response = client.get(
        f"/courses/{course_with_content.course.id}/chapters/999999",
        headers=student_headers,
    )

    assert response.status_code == 404


def test_get_chapter_belonging_to_another_course_is_404(
    client, student_headers, course_with_content, make_course, grant_access
):
    other_course = make_course(title="Other Course")
    grant_access(other_course)

    response = client.get(
        f"/courses/{other_course.id}"
        f"/chapters/{course_with_content.chapter_one.id}",
        headers=student_headers,
    )

    assert response.status_code == 404


def test_chapter_routes_require_a_token(client, course_with_content):
    course_id = course_with_content.course.id
    assert client.get(f"/courses/{course_id}/chapters").status_code == 401
