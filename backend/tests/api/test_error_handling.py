"""The typed domain errors and the single handler that maps them.

These pin the API contract in place. The refactor that introduced
app/errors.py changed how every service reports failure, and the point of
these tests is that none of it changed what a client sees.
"""

import pytest

from app.errors import ConflictError
from app.errors import DomainError
from app.errors import NotFoundError
from app.errors import PermissionDeniedError


def test_error_classes_carry_their_status_codes():
    assert NotFoundError().status_code == 404
    assert PermissionDeniedError().status_code == 403
    assert ConflictError().status_code == 400


def test_error_detail_defaults_when_none_is_given():
    assert NotFoundError().detail == "Not found"
    assert NotFoundError("Quiz not found").detail == "Quiz not found"


def test_every_domain_error_is_a_domain_error():
    for error_class in (NotFoundError, PermissionDeniedError, ConflictError):
        assert issubclass(error_class, DomainError)


@pytest.mark.parametrize(
    "path, expected_detail",
    [
        ("/admin/quizzes/999999", "Quiz not found"),
        ("/admin/quizzes/999999/results", "Quiz not found"),
        ("/admin/courses/999999/access", "Course not found"),
        ("/admin/students/999999/progress", "Student not found"),
        ("/admin/courses/999999/students", "Course not found"),
    ],
)
def test_not_found_responses_keep_their_shape(
    client, admin_headers, path, expected_detail
):
    """`{"detail": "..."}` is what FastAPI's own HTTPException produces, so
    the frontend's error reader keeps working unchanged."""
    response = client.get(path, headers=admin_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}


def test_not_found_on_a_write_route_keeps_its_shape(client, admin_headers):
    """The same handler covers PATCH and DELETE, which is where the user
    routes report a missing record."""
    patched = client.patch(
        "/admin/users/999999", headers=admin_headers, json={"name": "Ghost"}
    )
    deleted = client.delete("/admin/users/999999", headers=admin_headers)

    assert patched.status_code == 404
    assert patched.json() == {"detail": "User not found"}
    assert deleted.status_code == 404
    assert deleted.json() == {"detail": "User not found"}


def test_conflict_response_keeps_its_status_and_shape(
    client, admin_headers, student
):
    """Deliberately 400, not the more correct 409 — the frontend already
    reads 400 for a duplicate, and this refactor does not change the
    contract."""
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
    assert response.json() == {"detail": "Username already taken"}


def test_permission_denied_response_keeps_its_shape(
    client, other_student, headers_for, course_with_content
):
    response = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=headers_for(other_student),
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have access to this course"
    }


def test_locked_quiz_does_not_reveal_whether_the_course_exists(
    client, other_student, headers_for, course_with_content, make_quiz
):
    """A student with no access to the course and one who simply has not
    finished the chapter get the same answer, so the response cannot be
    used to discover courses."""
    quiz = make_quiz(course_with_content.chapter_one)

    no_access = client.get(
        f"/quizzes/{quiz.id}", headers=headers_for(other_student)
    )

    assert no_access.status_code == 403
    assert no_access.json() == {
        "detail": "Complete every lesson in this chapter first"
    }


def test_chapter_from_another_course_reads_as_missing(
    client, student_headers, course_with_content, make_course, grant_access
):
    other_course = make_course(title="Other")
    grant_access(other_course)

    response = client.get(
        f"/courses/{other_course.id}"
        f"/chapters/{course_with_content.chapter_one.id}",
        headers=student_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chapter not found"}


def test_validation_errors_still_come_from_fastapi(client, admin_headers):
    """422 is FastAPI's own, not ours — the handler must not swallow it."""
    response = client.post(
        "/admin/users",
        headers=admin_headers,
        json={"username": "nameless"},
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
