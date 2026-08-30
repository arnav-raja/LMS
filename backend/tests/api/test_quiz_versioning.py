"""Editing a quiz must not erase what students have already scored.

Saving from the builder used to delete the quiz row and create a new one,
which cascaded away every attempt recorded against it. A student who had
passed a chapter simply no longer had — their certificate requirement
quietly became unmet again.
"""


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


def finish_chapter_one(client, student_headers, content):
    for lesson in (content.lesson_one, content.lesson_two):
        complete(client, student_headers, lesson.id)


def build_payload(admin_view, title=None, passing_score=None):
    """The admin view turned back into a save payload, ids carried
    through — what the builder sends."""
    return {
        "title": title or admin_view["title"],
        "passing_score": (
            passing_score
            if passing_score is not None
            else admin_view["passing_score"]
        ),
        "questions": [
            {
                "id": question["id"],
                "question_text": question["question_text"],
                "options": [
                    {
                        "id": option["id"],
                        "option_text": option["option_text"],
                        "is_correct": option["is_correct"],
                    }
                    for option in question["options"]
                ],
            }
            for question in admin_view["questions"]
        ],
    }


def pass_the_quiz(client, student_headers, quiz_id):
    body = client.get(f"/quizzes/{quiz_id}", headers=student_headers).json()
    return client.post(
        f"/quizzes/{quiz_id}/submit",
        headers=student_headers,
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "option_id": question["options"][0]["id"],
                }
                for question in body["questions"]
            ]
        },
    )


def test_a_new_quiz_starts_at_version_one(
    client, admin_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()

    assert admin_view["version"] == 1


def test_editing_a_quiz_keeps_the_attempt_history(
    client, admin_headers, student_headers, course_with_content, make_quiz
):
    """The bug this change exists to prevent."""
    quiz = make_quiz(course_with_content.chapter_one)
    finish_chapter_one(client, student_headers, course_with_content)

    assert pass_the_quiz(client, student_headers, quiz.id).json()["passed"] is True

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()
    payload = build_payload(admin_view, title="Chapter One Check, Revised")
    payload["questions"][0]["question_text"] = "A completely different question?"

    saved = client.post(
        f"/admin/chapters/{course_with_content.chapter_one.id}/quiz",
        headers=admin_headers,
        json=payload,
    )
    assert saved.status_code == 200
    assert saved.json()["id"] == quiz.id, "the quiz row must survive the edit"

    results = client.get(
        f"/admin/quizzes/{quiz.id}/results", headers=admin_headers
    ).json()

    assert len(results["rows"]) == 1
    assert results["rows"][0]["passed"] is True
    assert results["rows"][0]["best_score"] == 100


def test_a_pass_still_counts_after_the_quiz_is_edited(
    client, admin_headers, student_headers, course_with_content, make_quiz
):
    """The student's side of the same thing: their chapter stays unlocked
    and their certificate requirement stays met."""
    quiz = make_quiz(course_with_content.chapter_one)
    finish_chapter_one(client, student_headers, course_with_content)
    pass_the_quiz(client, student_headers, quiz.id)

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()
    payload = build_payload(admin_view)
    payload["questions"][0]["question_text"] = "Reworded?"

    client.post(
        f"/admin/chapters/{course_with_content.chapter_one.id}/quiz",
        headers=admin_headers,
        json=payload,
    )

    chapters = client.get(
        f"/courses/{course_with_content.course.id}/chapters",
        headers=student_headers,
    ).json()

    assert chapters[1]["subchapters"][0]["is_locked"] is False
    assert chapters[0]["quiz"]["is_passed"] is True


def test_editing_content_bumps_the_version(
    client, admin_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)
    chapter_id = course_with_content.chapter_one.id

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()
    payload = build_payload(admin_view)
    payload["questions"][0]["question_text"] = "Changed?"

    saved = client.post(
        f"/admin/chapters/{chapter_id}/quiz", headers=admin_headers, json=payload
    )

    assert saved.json()["version"] == 2


def test_saving_without_changing_anything_leaves_the_version_alone(
    client, admin_headers, course_with_content, make_quiz
):
    """Opening the builder and pressing save should not pretend the quiz
    was rewritten."""
    quiz = make_quiz(course_with_content.chapter_one)
    chapter_id = course_with_content.chapter_one.id

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()

    saved = client.post(
        f"/admin/chapters/{chapter_id}/quiz",
        headers=admin_headers,
        json=build_payload(admin_view),
    )

    assert saved.json()["version"] == 1


def test_renaming_the_quiz_is_not_a_content_change(
    client, admin_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)
    chapter_id = course_with_content.chapter_one.id

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()

    saved = client.post(
        f"/admin/chapters/{chapter_id}/quiz",
        headers=admin_headers,
        json=build_payload(admin_view, title="A Better Name"),
    )

    assert saved.json()["title"] == "A Better Name"
    assert saved.json()["version"] == 1


def test_results_show_which_version_each_person_answered(
    client, admin_headers, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)
    finish_chapter_one(client, student_headers, course_with_content)
    pass_the_quiz(client, student_headers, quiz.id)

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()
    payload = build_payload(admin_view)
    payload["questions"][0]["question_text"] = "Rewritten?"

    client.post(
        f"/admin/chapters/{course_with_content.chapter_one.id}/quiz",
        headers=admin_headers,
        json=payload,
    )

    results = client.get(
        f"/admin/quizzes/{quiz.id}/results", headers=admin_headers
    ).json()

    # Passed version 1; the quiz is on version 2 now.
    assert results["rows"][0]["latest_version_attempted"] == 1

    listing = client.get("/admin/quizzes", headers=admin_headers).json()
    assert listing[0]["version"] == 2


def test_adding_and_removing_questions(
    client, admin_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one, questions=2)
    chapter_id = course_with_content.chapter_one.id

    admin_view = client.get(
        f"/admin/quizzes/{quiz.id}", headers=admin_headers
    ).json()

    payload = build_payload(admin_view)
    payload["questions"] = [payload["questions"][0]]
    payload["questions"].append(
        {
            "question_text": "A brand new question?",
            "options": [
                {"option_text": "Yes", "is_correct": True},
                {"option_text": "No", "is_correct": False},
            ],
        }
    )

    saved = client.post(
        f"/admin/chapters/{chapter_id}/quiz", headers=admin_headers, json=payload
    ).json()

    assert [q["question_text"] for q in saved["questions"]] == [
        "Question 1?",
        "A brand new question?",
    ]
    assert [q["question_number"] for q in saved["questions"]] == [1, 2]
    assert saved["version"] == 2


def test_a_question_id_from_another_quiz_is_rejected(
    client, admin_headers, course_with_content, make_quiz
):
    make_quiz(course_with_content.chapter_one)
    other_quiz = make_quiz(course_with_content.chapter_two)

    other_view = client.get(
        f"/admin/quizzes/{other_quiz.id}", headers=admin_headers
    ).json()

    response = client.post(
        f"/admin/chapters/{course_with_content.chapter_one.id}/quiz",
        headers=admin_headers,
        json=build_payload(other_view),
    )

    assert response.status_code == 404
    assert "not part of this quiz" in response.json()["detail"]


def test_deleting_a_quiz_outright_still_removes_it(
    client, admin_headers, student_headers, course_with_content, make_quiz
):
    """Deleting is still a deliberate full removal — only *editing* now
    preserves history."""
    quiz = make_quiz(course_with_content.chapter_one)
    finish_chapter_one(client, student_headers, course_with_content)
    pass_the_quiz(client, student_headers, quiz.id)

    assert (
        client.delete(
            f"/admin/quizzes/{quiz.id}", headers=admin_headers
        ).status_code
        == 200
    )
    assert (
        client.get(f"/admin/quizzes/{quiz.id}", headers=admin_headers).status_code
        == 404
    )
