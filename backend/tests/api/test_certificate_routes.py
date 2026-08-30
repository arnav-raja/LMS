"""Certificates are issued automatically the moment a course is finished —
there is no admin action that grants one — so these tests drive a course to
completion and check the certificate falls out of it."""


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


def finish_every_lesson(client, headers, content):
    responses = []
    for lesson in (content.lesson_one, content.lesson_two, content.lesson_three):
        responses.append(complete(client, headers, lesson.id))
    return responses


def test_no_certificate_before_the_course_is_finished(
    client, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    assert client.get("/certificates/me", headers=student_headers).json() == []


def test_certificate_is_issued_on_the_last_lesson(
    client, student_headers, course_with_content
):
    """A course with no quizzes completes on its final lesson, so the check
    has to run on the progress route too, not only after a quiz."""
    responses = finish_every_lesson(client, student_headers, course_with_content)

    assert responses[-1].json()["certificate_issued"] is True
    assert responses[0].json()["certificate_issued"] is False

    certificates = client.get(
        "/certificates/me", headers=student_headers
    ).json()

    assert len(certificates) == 1
    assert certificates[0]["course_title"] == "Security Basics"
    assert certificates[0]["certificate_number"].startswith("ARNAV-")


def test_certificate_is_only_flagged_as_new_once(
    client, student_headers, course_with_content
):
    finish_every_lesson(client, student_headers, course_with_content)

    again = complete(
        client, student_headers, course_with_content.lesson_three.id
    )

    assert again.json()["certificate_issued"] is False
    assert len(client.get("/certificates/me", headers=student_headers).json()) == 1


def test_an_unpassed_quiz_holds_the_certificate_back(
    client, student_headers, course_with_content, make_quiz
):
    make_quiz(course_with_content.chapter_two)

    finish_every_lesson(client, student_headers, course_with_content)

    assert client.get("/certificates/me", headers=student_headers).json() == []


def test_passing_the_last_quiz_issues_the_certificate(
    client, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_two)

    finish_every_lesson(client, student_headers, course_with_content)

    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()
    answers = [
        {
            "question_id": question["id"],
            "option_id": question["options"][0]["id"],
        }
        for question in body["questions"]
    ]

    response = client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": answers},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert response.json()["certificate_issued"] is True

    assert len(client.get("/certificates/me", headers=student_headers).json()) == 1


def test_my_certificates_requires_a_token(client):
    assert client.get("/certificates/me").status_code == 401


def test_students_only_see_their_own_certificates(
    client, student_headers, other_student, headers_for, course_with_content
):
    finish_every_lesson(client, student_headers, course_with_content)

    assert len(client.get("/certificates/me", headers=student_headers).json()) == 1
    assert (
        client.get("/certificates/me", headers=headers_for(other_student)).json()
        == []
    )


# -------------------------------------------------------------- registry --

def test_admin_registry_lists_every_certificate(
    client, admin_headers, student, student_headers, course_with_content
):
    finish_every_lesson(client, student_headers, course_with_content)

    response = client.get("/admin/certificates", headers=admin_headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["user_name"] == student.name
    assert rows[0]["user_id"] == student.id


def test_admin_registry_can_filter_by_course(
    client, admin_headers, student_headers, course_with_content, make_course
):
    finish_every_lesson(client, student_headers, course_with_content)
    other = make_course(title="Unrelated")

    matching = client.get(
        f"/admin/certificates?course_id={course_with_content.course.id}",
        headers=admin_headers,
    ).json()
    non_matching = client.get(
        f"/admin/certificates?course_id={other.id}",
        headers=admin_headers,
    ).json()

    assert len(matching) == 1
    assert non_matching == []


def test_admin_registry_forbidden_for_student(client, student_headers):
    assert (
        client.get("/admin/certificates", headers=student_headers).status_code == 403
    )
