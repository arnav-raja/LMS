"""Quiz builder, quiz taking, and the gate that keeps a quiz shut until
its chapter's lessons are done."""

import pytest


QUIZ_PAYLOAD = {
    "title": "Chapter One Check",
    "passing_score": 70,
    "questions": [
        {
            "question_text": "Where is the nearest exit?",
            "options": [
                {"option_text": "Down the hall", "is_correct": True},
                {"option_text": "Through the window", "is_correct": False},
            ],
        },
        {
            "question_text": "Who do you report to?",
            "options": [
                {"option_text": "The fire warden", "is_correct": True},
                {"option_text": "Nobody", "is_correct": False},
            ],
        },
    ],
}


@pytest.fixture
def finished_chapter_one(client, student_headers, course_with_content):
    """Completes chapter one's lessons, which is what unlocks its quiz."""
    for lesson in (course_with_content.lesson_one, course_with_content.lesson_two):
        client.post(
            "/progress/complete",
            headers=student_headers,
            json={"subchapter_id": lesson.id},
        )
    return course_with_content


def answers_for(quiz_body, correct=True):
    """Builds a submission. The seeded options are ordered with the correct
    one first, so index 0 passes and index 1 fails."""
    return [
        {
            "question_id": question["id"],
            "option_id": question["options"][0 if correct else 1]["id"],
        }
        for question in quiz_body["questions"]
    ]


# --------------------------------------------------------------- admin ----

def test_create_quiz_on_a_chapter(client, admin_headers, course_with_content):
    response = client.post(
        f"/admin/chapters/{course_with_content.chapter_one.id}/quiz",
        headers=admin_headers,
        json=QUIZ_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Chapter One Check"
    assert len(body["questions"]) == 2
    assert body["questions"][0]["question_number"] == 1


def test_create_quiz_on_unknown_chapter(client, admin_headers):
    response = client.post(
        "/admin/chapters/999999/quiz",
        headers=admin_headers,
        json=QUIZ_PAYLOAD,
    )

    assert response.status_code == 404


def test_create_quiz_forbidden_for_student(
    client, student_headers, course_with_content
):
    response = client.post(
        f"/admin/chapters/{course_with_content.chapter_one.id}/quiz",
        headers=student_headers,
        json=QUIZ_PAYLOAD,
    )

    assert response.status_code == 403


def test_admin_quiz_list(client, admin_headers, course_with_content, make_quiz):
    make_quiz(course_with_content.chapter_one)

    response = client.get("/admin/quizzes", headers=admin_headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["course_title"] == "Security Basics"
    assert rows[0]["chapter_title"] == "Chapter One"
    assert rows[0]["question_count"] == 2


def test_admin_quiz_list_forbidden_for_student(client, student_headers):
    assert client.get("/admin/quizzes", headers=student_headers).status_code == 403


def test_admin_quiz_detail_shows_the_correct_answers(
    client, admin_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    response = client.get(f"/admin/quizzes/{quiz.id}", headers=admin_headers)

    assert response.status_code == 200
    options = response.json()["questions"][0]["options"]
    assert any(option["is_correct"] for option in options)


def test_admin_quiz_detail_not_found(client, admin_headers):
    assert (
        client.get("/admin/quizzes/999999", headers=admin_headers).status_code == 404
    )


def test_delete_quiz(client, admin_headers, course_with_content, make_quiz):
    quiz = make_quiz(course_with_content.chapter_one)

    response = client.delete(f"/admin/quizzes/{quiz.id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {"deleted": True}
    assert (
        client.get(f"/admin/quizzes/{quiz.id}", headers=admin_headers).status_code
        == 404
    )


def test_delete_quiz_not_found(client, admin_headers):
    assert (
        client.delete("/admin/quizzes/999999", headers=admin_headers).status_code
        == 404
    )


def test_delete_quiz_forbidden_for_student(
    client, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    assert (
        client.delete(
            f"/admin/quizzes/{quiz.id}", headers=student_headers
        ).status_code
        == 403
    )


def test_quiz_results_report_each_student(
    client, admin_headers, student, student_headers, finished_chapter_one, make_quiz
):
    quiz = make_quiz(finished_chapter_one.chapter_one)

    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()
    client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": answers_for(body, correct=False)},
    )
    client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": answers_for(body, correct=True)},
    )

    response = client.get(
        f"/admin/quizzes/{quiz.id}/results", headers=admin_headers
    )

    assert response.status_code == 200
    rows = response.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["user_name"] == student.name
    assert rows[0]["attempts_count"] == 2
    assert rows[0]["best_score"] == 100
    assert rows[0]["passed"] is True


def test_quiz_results_are_empty_before_anyone_attempts(
    client, admin_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    response = client.get(
        f"/admin/quizzes/{quiz.id}/results", headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["rows"] == []


def test_quiz_results_not_found(client, admin_headers):
    assert (
        client.get(
            "/admin/quizzes/999999/results", headers=admin_headers
        ).status_code
        == 404
    )


def test_quiz_results_forbidden_for_student(
    client, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    assert (
        client.get(
            f"/admin/quizzes/{quiz.id}/results", headers=student_headers
        ).status_code
        == 403
    )


# ------------------------------------------------------------- student ----

def test_quiz_is_locked_until_the_chapter_is_finished(
    client, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    response = client.get(f"/quizzes/{quiz.id}", headers=student_headers)

    assert response.status_code == 403
    assert "every lesson" in response.json()["detail"]


def test_quiz_opens_once_the_chapter_is_finished(
    client, student_headers, finished_chapter_one, make_quiz
):
    quiz = make_quiz(finished_chapter_one.chapter_one)

    response = client.get(f"/quizzes/{quiz.id}", headers=student_headers)

    assert response.status_code == 200
    assert response.json()["title"] == "Chapter One Quiz"


def test_take_view_hides_which_option_is_correct(
    client, student_headers, finished_chapter_one, make_quiz
):
    """A student must not be able to read the answer key off the wire."""
    quiz = make_quiz(finished_chapter_one.chapter_one)

    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()

    for question in body["questions"]:
        for option in question["options"]:
            assert "is_correct" not in option


def test_take_quiz_not_found(client, student_headers):
    assert client.get("/quizzes/999999", headers=student_headers).status_code == 404


def test_submitting_every_correct_answer_passes(
    client, student_headers, finished_chapter_one, make_quiz
):
    quiz = make_quiz(finished_chapter_one.chapter_one)
    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()

    response = client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": answers_for(body, correct=True)},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["score"] == 100
    assert result["passed"] is True


def test_submitting_every_wrong_answer_fails(
    client, student_headers, finished_chapter_one, make_quiz
):
    quiz = make_quiz(finished_chapter_one.chapter_one)
    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()

    response = client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": answers_for(body, correct=False)},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["score"] == 0
    assert result["passed"] is False


def test_submitting_a_locked_quiz_is_forbidden(
    client, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    response = client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": []},
    )

    assert response.status_code == 403


def test_passing_a_quiz_unlocks_the_next_chapter(
    client, student_headers, finished_chapter_one, make_quiz
):
    """Chapter two stays shut behind chapter one's quiz, not just behind
    chapter one's lessons."""
    quiz = make_quiz(finished_chapter_one.chapter_one)
    course_id = finished_chapter_one.course.id

    before = client.get(
        f"/courses/{course_id}/chapters", headers=student_headers
    ).json()
    assert before[1]["subchapters"][0]["is_locked"] is True

    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()
    client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": answers_for(body, correct=True)},
    )

    after = client.get(
        f"/courses/{course_id}/chapters", headers=student_headers
    ).json()
    assert after[1]["subchapters"][0]["is_locked"] is False


def test_student_quiz_list_reports_status(
    client, student_headers, course_with_content, make_quiz
):
    make_quiz(course_with_content.chapter_one)

    response = client.get("/quizzes/me", headers=student_headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["status"] == "locked"
    assert rows[0]["course_title"] == "Security Basics"


def test_student_quiz_list_status_moves_to_available_then_passed(
    client, student_headers, finished_chapter_one, make_quiz
):
    quiz = make_quiz(finished_chapter_one.chapter_one)

    assert client.get("/quizzes/me", headers=student_headers).json()[0][
        "status"
    ] == "available"

    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()
    client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={"answers": answers_for(body, correct=True)},
    )

    row = client.get("/quizzes/me", headers=student_headers).json()[0]
    assert row["status"] == "passed"
    assert row["best_score"] == 100


def test_student_quiz_list_requires_a_token(client):
    assert client.get("/quizzes/me").status_code == 401
