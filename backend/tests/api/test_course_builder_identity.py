"""Editing a course must not disturb what students have already done.

The builder used to match chapters and subchapters to the request by
position. Reordering two chapters therefore handed each one's completion
history to the other: a student who had finished "Fire Safety" was
suddenly recorded as having finished "Data Handling" instead, with
nothing anywhere to indicate it had happened.

They are matched by id now. These tests are the reason that has to stay
true.
"""


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


def read_structure(client, headers, course_id):
    """The course as the builder loads it, ids included.

    Note that `is_completed` on each lesson is computed for whoever is
    asking — read it with the student's headers, never the admin's, or it
    will always be False.
    """
    return client.get(f"/courses/{course_id}/chapters", headers=headers).json()


def completion_by_lesson(client, student_headers, course_id):
    """{subchapter id: is_completed} as the student sees it."""
    return {
        lesson["id"]: lesson["is_completed"]
        for chapter in read_structure(client, student_headers, course_id)
        for lesson in chapter["subchapters"]
    }


def to_payload(chapters, title="Course", status="published"):
    """Turn a loaded structure back into a save payload, exactly as the
    builder does — carrying every id through."""
    return {
        "title": title,
        "description": "Description",
        "status": status,
        "chapters": [
            {
                "id": chapter["id"],
                "title": chapter["title"],
                "description": chapter["description"],
                "subchapters": [
                    {
                        "id": subchapter["id"],
                        "title": subchapter["title"],
                        "content": subchapter["content"],
                    }
                    for subchapter in chapter["subchapters"]
                ],
            }
            for chapter in chapters
        ],
    }


def test_reordering_chapters_keeps_progress_on_the_right_lesson(
    client, admin_headers, student_headers, course_with_content
):
    """The bug this whole change exists to prevent."""
    course_id = course_with_content.course.id
    finished_id = course_with_content.lesson_one.id

    complete(client, student_headers, finished_id)

    structure = read_structure(client, admin_headers, course_id)
    payload = to_payload([structure[1], structure[0]], title="Reordered")

    response = client.put(
        f"/admin/courses/{course_id}", headers=admin_headers, json=payload
    )
    assert response.status_code == 200

    progress = client.get("/progress/me", headers=student_headers).json()

    assert [row["subchapter_id"] for row in progress] == [finished_id]


def test_reordering_chapters_renumbers_them(
    client, admin_headers, course_with_content
):
    course_id = course_with_content.course.id
    structure = read_structure(client, admin_headers, course_id)

    client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload([structure[1], structure[0]]),
    )

    after = read_structure(client, admin_headers, course_id)

    assert [chapter["title"] for chapter in after] == [
        "Chapter Two",
        "Chapter One",
    ]
    assert [chapter["chapter_number"] for chapter in after] == [1, 2]
    # Same rows, moved — not new ones.
    assert {chapter["id"] for chapter in after} == {
        chapter["id"] for chapter in structure
    }


def test_reordering_subchapters_keeps_each_lesson_its_own_progress(
    client, admin_headers, student_headers, course_with_content
):
    course_id = course_with_content.course.id
    first_id = course_with_content.lesson_one.id

    complete(client, student_headers, first_id)

    structure = read_structure(client, admin_headers, course_id)
    chapter_one = structure[0]
    chapter_one["subchapters"] = [
        chapter_one["subchapters"][1],
        chapter_one["subchapters"][0],
    ]

    client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload([chapter_one] + structure[1:]),
    )

    after = read_structure(client, admin_headers, course_id)
    lessons = after[0]["subchapters"]

    assert [lesson["title"] for lesson in lessons] == ["Lesson Two", "Lesson One"]

    completed = completion_by_lesson(client, student_headers, course_id)
    assert completed[first_id] is True


def test_editing_a_title_keeps_the_same_row(
    client, admin_headers, student_headers, course_with_content
):
    course_id = course_with_content.course.id
    lesson_id = course_with_content.lesson_one.id

    complete(client, student_headers, lesson_id)

    structure = read_structure(client, admin_headers, course_id)
    structure[0]["subchapters"][0]["title"] = "Lesson One, Revised"

    client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload(structure),
    )

    after = read_structure(client, admin_headers, course_id)
    lesson = after[0]["subchapters"][0]

    assert lesson["id"] == lesson_id
    assert lesson["title"] == "Lesson One, Revised"

    completed = completion_by_lesson(client, student_headers, course_id)
    assert completed[lesson_id] is True


def test_adding_a_lesson_leaves_the_existing_ones_alone(
    client, admin_headers, student_headers, course_with_content
):
    course_id = course_with_content.course.id
    lesson_id = course_with_content.lesson_one.id

    complete(client, student_headers, lesson_id)

    structure = read_structure(client, admin_headers, course_id)
    structure[0]["subchapters"].insert(
        0, {"id": None, "title": "New First Lesson", "content": "New"}
    )

    client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload(structure),
    )

    after = read_structure(client, admin_headers, course_id)
    lessons = after[0]["subchapters"]

    assert [lesson["title"] for lesson in lessons] == [
        "New First Lesson",
        "Lesson One",
        "Lesson Two",
    ]

    progress = client.get("/progress/me", headers=student_headers).json()
    assert [row["subchapter_id"] for row in progress] == [lesson_id]


def test_removing_a_lesson_removes_only_its_progress(
    client, admin_headers, student_headers, course_with_content
):
    course_id = course_with_content.course.id
    kept_id = course_with_content.lesson_one.id
    removed_id = course_with_content.lesson_two.id

    complete(client, student_headers, kept_id)
    complete(client, student_headers, removed_id)

    structure = read_structure(client, admin_headers, course_id)
    structure[0]["subchapters"] = [structure[0]["subchapters"][0]]

    client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload(structure),
    )

    progress = client.get("/progress/me", headers=student_headers).json()
    remaining = [row["subchapter_id"] for row in progress]

    assert kept_id in remaining
    assert removed_id not in remaining


def test_removing_a_chapter_removes_its_lessons_and_their_progress(
    client, admin_headers, student_headers, course_with_content
):
    course_id = course_with_content.course.id
    kept_id = course_with_content.lesson_one.id

    complete(client, student_headers, kept_id)

    structure = read_structure(client, admin_headers, course_id)

    client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload([structure[0]]),
    )

    after = read_structure(client, admin_headers, course_id)
    assert [chapter["title"] for chapter in after] == ["Chapter One"]

    progress = client.get("/progress/me", headers=student_headers).json()
    assert [row["subchapter_id"] for row in progress] == [kept_id]


def test_a_chapter_id_from_another_course_is_rejected(
    client, admin_headers, course_with_content, make_course
):
    """Ids arrive from the client, so a save must not be able to reach
    into a course it was not editing."""
    other_course = make_course(title="Other Course")

    response = client.put(
        f"/admin/courses/{other_course.id}",
        headers=admin_headers,
        json={
            "title": "Hijack",
            "description": "D",
            "status": "draft",
            "chapters": [
                {
                    "id": course_with_content.chapter_one.id,
                    "title": "Stolen",
                    "description": None,
                    "subchapters": [],
                }
            ],
        },
    )

    assert response.status_code == 404
    assert "not part of this course" in response.json()["detail"]


def test_a_subchapter_id_from_another_chapter_is_rejected(
    client, admin_headers, course_with_content
):
    course_id = course_with_content.course.id
    structure = read_structure(client, admin_headers, course_id)

    # Chapter one's payload, but carrying chapter two's lesson.
    structure[0]["subchapters"] = [
        {
            "id": course_with_content.lesson_three.id,
            "title": "Stolen",
            "content": None,
        }
    ]

    response = client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload(structure),
    )

    assert response.status_code == 404
    assert "not part of this chapter" in response.json()["detail"]


def test_a_rejected_edit_changes_nothing(
    client, admin_headers, student_headers, course_with_content
):
    """The failure must leave the course exactly as it was, not half
    applied."""
    course_id = course_with_content.course.id
    complete(client, student_headers, course_with_content.lesson_one.id)

    before = read_structure(client, admin_headers, course_id)

    structure = read_structure(client, admin_headers, course_id)
    structure[0]["title"] = "Renamed Before The Failure"
    structure[0]["subchapters"] = [
        {"id": course_with_content.lesson_three.id, "title": "Stolen", "content": None}
    ]

    failed = client.put(
        f"/admin/courses/{course_id}",
        headers=admin_headers,
        json=to_payload(structure),
    )
    assert failed.status_code == 404

    after = read_structure(client, admin_headers, course_id)

    assert [chapter["title"] for chapter in after] == [
        chapter["title"] for chapter in before
    ]

    completed = completion_by_lesson(client, student_headers, course_id)
    assert completed[course_with_content.lesson_one.id] is True


def test_a_new_course_still_saves_without_any_ids(client, admin_headers):
    """Creating is unchanged — nothing has an id yet."""
    response = client.post(
        "/admin/courses",
        headers=admin_headers,
        json={
            "title": "Brand New",
            "description": "D",
            "status": "published",
            "chapters": [
                {
                    "title": "One",
                    "description": None,
                    "subchapters": [{"title": "Lesson", "content": "Body"}],
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["num_chapters"] == 1
