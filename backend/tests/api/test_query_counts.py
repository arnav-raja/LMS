"""The number of queries a page costs must not grow with the data.

Every endpoint here was correct and passed all its tests with two rows in
the database. The failure mode is invisible at that size: a loop that
issues one query per course is indistinguishable from one query until a
real course catalogue arrives, at which point the page falls over.

Each test below builds a deliberately lopsided dataset — a small one and
a larger one — and asserts the query count barely moves between them.
The exact bounds are generous on purpose; they exist to catch growth,
not to police a number.
"""

import pytest


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


@pytest.fixture
def catalogue(make_course, make_chapter, make_subchapter, grant_access):
    """Builds `courses` courses, each with `chapters` chapters of
    `lessons` lessons, all reachable by the default student."""

    def _build(courses=1, chapters=2, lessons=2, prefix="Course"):
        built = []
        for course_index in range(courses):
            course = make_course(title=f"{prefix} {course_index}")
            grant_access(course)
            for chapter_index in range(1, chapters + 1):
                chapter = make_chapter(
                    course, chapter_index, f"Chapter {chapter_index}"
                )
                for lesson_index in range(1, lessons + 1):
                    make_subchapter(
                        chapter, lesson_index, f"Lesson {lesson_index}"
                    )
            built.append(course)
        return built

    return _build


def measure(count_queries, call):
    with count_queries() as queries:
        response = call()
    assert response.status_code == 200, response.text
    return queries


# ------------------------------------------------------ student dashboard --

def test_student_dashboard_does_not_query_per_course(
    client, student_headers, catalogue, count_queries
):
    catalogue(courses=1, chapters=2, lessons=2)
    small = measure(
        count_queries,
        lambda: client.get("/me/dashboard", headers=student_headers),
    )

    catalogue(courses=6, chapters=3, lessons=3, prefix="Extra")
    large = measure(
        count_queries,
        lambda: client.get("/me/dashboard", headers=student_headers),
    )

    assert large.count <= small.count + 1, (
        f"dashboard went from {small.count} to {large.count} queries when "
        f"the catalogue grew — it is querying per course:\n{large.report()}"
    )


def test_student_dashboard_still_reports_correctly(
    client, student_headers, course_with_content
):
    """The batching must not change the answer."""
    complete(client, student_headers, course_with_content.lesson_one.id)

    body = client.get("/me/dashboard", headers=student_headers).json()
    course = body["courses"][0]

    assert course["progress"] == 33.33
    assert course["next_subchapter"] == "Lesson Two"


def test_dashboard_next_lesson_follows_course_order(
    client, student_headers, course_with_content
):
    """`next_subchapter` has to be the first unfinished lesson in course
    order. It used to walk an unordered relationship, so the answer
    depended on whatever order the database happened to return rows in."""
    body = client.get("/me/dashboard", headers=student_headers).json()

    assert body["courses"][0]["next_subchapter"] == "Lesson One"


# --------------------------------------------------------- course roster --

def test_course_roster_does_not_query_per_student(
    client, admin_headers, make_user, course_with_content, count_queries
):
    small = measure(
        count_queries,
        lambda: client.get(
            f"/admin/courses/{course_with_content.course.id}/students",
            headers=admin_headers,
        ),
    )

    for index in range(12):
        make_user(
            name=f"Student {index}",
            username=f"student{index}",
            email=f"student{index}@example.com",
            department="EC",
            seniority="Mid",
        )

    large = measure(
        count_queries,
        lambda: client.get(
            f"/admin/courses/{course_with_content.course.id}/students",
            headers=admin_headers,
        ),
    )

    assert large.count <= small.count + 1, (
        f"roster went from {small.count} to {large.count} queries with 12 "
        f"more students — it is querying per student:\n{large.report()}"
    )


def test_course_roster_still_reports_correctly(
    client, admin_headers, student, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    body = client.get(
        f"/admin/courses/{course_with_content.course.id}/students",
        headers=admin_headers,
    ).json()

    row = next(r for r in body["students"] if r["name"] == student.name)
    assert row["completed_subchapters"] == 1
    assert row["total_subchapters"] == 3
    assert row["percentage"] == 33.33
    assert row["last_activity"] is not None


# ------------------------------------------------ student progress detail --

def test_student_progress_detail_does_not_query_per_course(
    client, admin_headers, student, catalogue, count_queries
):
    catalogue(courses=1, chapters=2, lessons=2)
    small = measure(
        count_queries,
        lambda: client.get(
            f"/admin/students/{student.id}/progress", headers=admin_headers
        ),
    )

    catalogue(courses=6, chapters=3, lessons=3, prefix="Extra")
    large = measure(
        count_queries,
        lambda: client.get(
            f"/admin/students/{student.id}/progress", headers=admin_headers
        ),
    )

    assert large.count <= small.count + 1, (
        f"progress detail went from {small.count} to {large.count} queries "
        f"when the catalogue grew:\n{large.report()}"
    )


def test_student_progress_detail_still_reports_correctly(
    client, admin_headers, student, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    body = client.get(
        f"/admin/students/{student.id}/progress", headers=admin_headers
    ).json()

    course = body["courses"][0]
    assert course["percentage"] == 33.33
    assert course["chapters"][0]["subchapters"][0]["is_completed"] is True
    assert course["chapters"][0]["subchapters"][1]["is_completed"] is False
    assert course["chapters"][0]["subchapters"][1]["is_locked"] is False


# ------------------------------------------------------------ admin lists --

def test_admin_quiz_list_does_not_load_every_attempt(
    client, admin_headers, student_headers, catalogue, make_quiz, count_queries
):
    """Already batched, and this keeps it that way."""
    catalogue(courses=2, chapters=2, lessons=1)

    small = measure(
        count_queries,
        lambda: client.get("/admin/quizzes", headers=admin_headers),
    )

    catalogue(courses=5, chapters=3, lessons=1, prefix="Extra")

    large = measure(
        count_queries,
        lambda: client.get("/admin/quizzes", headers=admin_headers),
    )

    assert large.count <= small.count + 1, (
        f"quiz list went from {small.count} to {large.count} queries:\n"
        f"{large.report()}"
    )


def test_course_list_does_not_query_per_course(
    client, student_headers, catalogue, count_queries
):
    catalogue(courses=1)
    small = measure(
        count_queries, lambda: client.get("/courses", headers=student_headers)
    )

    catalogue(courses=10, prefix="Extra")
    large = measure(
        count_queries, lambda: client.get("/courses", headers=student_headers)
    )

    assert large.count <= small.count + 1, (
        f"course list went from {small.count} to {large.count} queries:\n"
        f"{large.report()}"
    )


def test_student_quiz_list_does_not_query_per_chapter(
    client, student_headers, catalogue, make_quiz, count_queries
):
    catalogue(courses=1, chapters=2, lessons=1)
    small = measure(
        count_queries, lambda: client.get("/quizzes/me", headers=student_headers)
    )

    catalogue(courses=5, chapters=3, lessons=1, prefix="Extra")
    large = measure(
        count_queries, lambda: client.get("/quizzes/me", headers=student_headers)
    )

    assert large.count <= small.count + 1, (
        f"student quiz list went from {small.count} to {large.count} "
        f"queries:\n{large.report()}"
    )


# ------------------------------------------------------------ the player --

def test_course_player_does_not_query_per_chapter(
    client, student_headers, make_course, make_chapter, make_subchapter,
    grant_access, count_queries
):
    small_course = make_course(title="Small")
    grant_access(small_course)
    for chapter_index in range(1, 3):
        chapter = make_chapter(small_course, chapter_index, f"Ch {chapter_index}")
        make_subchapter(chapter, 1, "Lesson")

    small = measure(
        count_queries,
        lambda: client.get(
            f"/courses/{small_course.id}/chapters", headers=student_headers
        ),
    )

    big_course = make_course(title="Big")
    grant_access(big_course)
    for chapter_index in range(1, 9):
        chapter = make_chapter(big_course, chapter_index, f"Ch {chapter_index}")
        for lesson_index in range(1, 4):
            make_subchapter(chapter, lesson_index, f"Lesson {lesson_index}")

    large = measure(
        count_queries,
        lambda: client.get(
            f"/courses/{big_course.id}/chapters", headers=student_headers
        ),
    )

    assert large.count <= small.count + 2, (
        f"course player went from {small.count} to {large.count} queries "
        f"for a course four times the size:\n{large.report()}"
    )


# ------------------------------------------------ admin chapter listing ----

def test_admin_chapter_list_is_one_request_and_one_query(
    client, admin_headers, catalogue, count_queries
):
    """The Quizzes page needs every chapter to attach a quiz to. It used to
    build that client-side with one HTTP request per course — forty
    courses meant forty round trips, each computing lock maps and quiz
    summaries that were thrown away."""
    catalogue(courses=1, chapters=2, lessons=1)
    small = measure(
        count_queries, lambda: client.get("/admin/chapters", headers=admin_headers)
    )

    catalogue(courses=8, chapters=4, lessons=2, prefix="Extra")
    large = measure(
        count_queries, lambda: client.get("/admin/chapters", headers=admin_headers)
    )

    assert large.count <= small.count, (
        f"chapter list went from {small.count} to {large.count} queries:\n"
        f"{large.report()}"
    )


def test_admin_chapter_list_reports_course_and_quiz_state(
    client, admin_headers, course_with_content, make_quiz
):
    make_quiz(course_with_content.chapter_one)

    rows = client.get("/admin/chapters", headers=admin_headers).json()

    by_id = {row["id"]: row for row in rows}
    assert by_id[course_with_content.chapter_one.id]["has_quiz"] is True
    assert by_id[course_with_content.chapter_two.id]["has_quiz"] is False
    assert by_id[course_with_content.chapter_one.id]["course_title"] == (
        "Security Basics"
    )


def test_admin_chapter_list_is_admin_only(client, student_headers):
    assert client.get("/admin/chapters", headers=student_headers).status_code == 403
