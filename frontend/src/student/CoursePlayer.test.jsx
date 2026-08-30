import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CoursePlayer from "./CoursePlayer";
import { courseApi, learningApi, progressApi } from "../api/endpoints";
import { renderAt } from "../test/render";

vi.mock("../api/endpoints", () => ({
  courseApi: { list: vi.fn(), chapters: vi.fn() },
  learningApi: { progress: vi.fn(), continueCourse: vi.fn() },
  progressApi: { complete: vi.fn() },
}));

const COURSE = { id: 2, title: "Fire Safety", status: "published" };

function lesson(id, title, { locked = false, done = false, content = "Body" } = {}) {
  return {
    id,
    chapter_id: 1,
    subchapter_number: id,
    title,
    // The API withholds the text of a locked lesson entirely — the lock is
    // enforced on the server, not by hiding it here.
    content: locked ? null : content,
    is_completed: done,
    is_locked: locked,
  };
}

function chapters({ quizUnlocked = false, withQuiz = false, lessons } = {}) {
  return [
    {
      id: 1,
      course_id: 2,
      chapter_number: 1,
      title: "Before The Alarm",
      description: null,
      num_subchapters: 2,
      subchapters: lessons || [
        lesson(1, "Know Your Exits"),
        lesson(2, "Assembly Points", { locked: true }),
      ],
      quiz: withQuiz
        ? {
            id: 9,
            title: "Chapter One Check",
            passing_score: 70,
            is_unlocked: quizUnlocked,
            is_passed: false,
            best_score: null,
            attempts_count: 0,
          }
        : null,
    },
  ];
}

function renderPlayer(state) {
  return renderAt(<CoursePlayer />, {
    path: "/courses/:courseId",
    at: "/courses/2",
    state,
  });
}

beforeEach(() => {
  courseApi.list.mockResolvedValue([COURSE]);
  courseApi.chapters.mockResolvedValue(chapters());
  learningApi.progress.mockResolvedValue({
    course_id: 2,
    completed_subchapters: 0,
    total_subchapters: 2,
    completed_chapters: 0,
    total_chapters: 1,
    percentage: 0,
  });
  learningApi.continueCourse.mockResolvedValue({ subchapter_id: 1 });
  progressApi.complete.mockReset();
});

describe("opening a course", () => {
  it("resumes at the lesson the API says to continue from", async () => {
    renderPlayer();

    expect(await screen.findByText("Fire Safety")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Know Your Exits" })
    ).toBeInTheDocument();
  });

  it("shows how far through the course the student is", async () => {
    learningApi.progress.mockResolvedValue({
      course_id: 2,
      completed_subchapters: 1,
      total_subchapters: 2,
      completed_chapters: 0,
      total_chapters: 1,
      percentage: 50,
    });

    renderPlayer();

    expect(
      await screen.findByText("1 of 2 lessons complete")
    ).toBeInTheDocument();
  });

  it("treats a finished course as a state, not an error", async () => {
    // The continue endpoint answers 404 once everything is done.
    learningApi.continueCourse.mockRejectedValue(
      Object.assign(new Error("Course completed"), {
        status: 404,
        isNotFound: true,
      })
    );
    learningApi.progress.mockResolvedValue({
      course_id: 2,
      completed_subchapters: 2,
      total_subchapters: 2,
      completed_chapters: 1,
      total_chapters: 1,
      percentage: 100,
    });

    renderPlayer();

    expect(
      await screen.findByText(/completed every lesson in this course/i)
    ).toBeInTheDocument();
    expect(screen.queryByText("Could not open this course")).toBeNull();
  });

  it("explains a course it cannot open", async () => {
    courseApi.chapters.mockRejectedValue(
      Object.assign(new Error("You do not have access to this course"), {
        status: 403,
        isForbidden: true,
      })
    );

    renderPlayer();

    expect(
      await screen.findByText("Could not open this course")
    ).toBeInTheDocument();
  });
});

describe("locked lessons", () => {
  it("does not open one when it is clicked", async () => {
    const user = userEvent.setup();
    renderPlayer();

    await screen.findByRole("heading", { name: "Know Your Exits" });

    const rail = screen.getByLabelText("Course contents");
    await user.click(within(rail).getByText("Assembly Points"));

    // Still on the unlocked lesson.
    expect(
      screen.getByRole("heading", { name: "Know Your Exits" })
    ).toBeInTheDocument();
  });
});

describe("completing a lesson", () => {
  it("records it and advances to the next one", async () => {
    const user = userEvent.setup();

    progressApi.complete.mockResolvedValue({
      id: 1,
      subchapter_id: 1,
      is_completed: true,
      certificate_issued: false,
    });
    // After completing lesson one, lesson two is unlocked.
    courseApi.chapters
      .mockResolvedValueOnce(chapters())
      .mockResolvedValue(
        chapters({
          lessons: [
            lesson(1, "Know Your Exits", { done: true }),
            lesson(2, "Assembly Points"),
          ],
        })
      );

    renderPlayer();
    await screen.findByRole("heading", { name: "Know Your Exits" });

    await user.click(screen.getByRole("button", { name: /mark.*complete/i }));

    await waitFor(() => expect(progressApi.complete).toHaveBeenCalledWith(1));
    expect(
      await screen.findByRole("heading", { name: "Assembly Points" })
    ).toBeInTheDocument();
  });

  it("hands off to the chapter quiz rather than opening it", async () => {
    const user = userEvent.setup();

    progressApi.complete.mockResolvedValue({
      id: 2,
      subchapter_id: 1,
      is_completed: true,
      certificate_issued: false,
    });
    courseApi.chapters
      .mockResolvedValueOnce(
        chapters({
          withQuiz: true,
          lessons: [lesson(1, "Know Your Exits")],
        })
      )
      .mockResolvedValue(
        chapters({
          withQuiz: true,
          quizUnlocked: true,
          lessons: [lesson(1, "Know Your Exits", { done: true })],
        })
      );

    renderPlayer();
    await screen.findByRole("heading", { name: "Know Your Exits" });

    await user.click(screen.getByRole("button", { name: /mark.*complete/i }));

    // A quiz is never opened automatically — the student is offered it.
    expect(
      await screen.findByRole("heading", {
        name: "Congratulations on completing Before The Alarm",
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Attempt quiz" })
    ).toBeInTheDocument();
  });

  it("shows the certificate hand-off when the course finishes", async () => {
    const user = userEvent.setup();

    progressApi.complete.mockResolvedValue({
      id: 3,
      subchapter_id: 1,
      is_completed: true,
      certificate_issued: true,
    });

    renderPlayer();
    await screen.findByRole("heading", { name: "Know Your Exits" });

    await user.click(screen.getByRole("button", { name: /mark.*complete/i }));

    expect(
      await screen.findByRole("heading", {
        name: "Congratulations on completing the course",
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "View certificate" })
    ).toBeInTheDocument();
  });

  it("surfaces a rejection instead of silently doing nothing", async () => {
    const user = userEvent.setup();
    progressApi.complete.mockRejectedValue(
      new Error("Complete the previous subchapter first")
    );

    renderPlayer();
    await screen.findByRole("heading", { name: "Know Your Exits" });

    await user.click(screen.getByRole("button", { name: /mark.*complete/i }));

    expect(
      await screen.findByText("Complete the previous subchapter first")
    ).toBeInTheDocument();
  });
});

describe("arriving back from a passed quiz", () => {
  it("shows the certificate hand-off when the quiz finished the course", async () => {
    renderPlayer({ showCertificateInterstitial: true });

    expect(
      await screen.findByRole("heading", {
        name: "Congratulations on completing the course",
      })
    ).toBeInTheDocument();
  });
});
