import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CourseBuilder from "./CourseBuilder";
import { courseApi, courseBuilderApi } from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  courseApi: { chapters: vi.fn() },
  courseBuilderApi: { create: vi.fn(), update: vi.fn() },
}));

const COURSE = {
  id: 2,
  title: "Fire Safety",
  description: "What to do when the alarm sounds",
  status: "published",
  num_chapters: 2,
};

const STRUCTURE = [
  {
    id: 10,
    course_id: 2,
    chapter_number: 1,
    title: "Before The Alarm",
    description: "Preparation",
    num_subchapters: 2,
    subchapters: [
      { id: 100, chapter_id: 10, subchapter_number: 1, title: "Know Your Exits", content: "A" },
      { id: 101, chapter_id: 10, subchapter_number: 2, title: "Assembly Points", content: "B" },
    ],
    quiz: null,
  },
  {
    id: 11,
    course_id: 2,
    chapter_number: 2,
    title: "After The Alarm",
    description: null,
    num_subchapters: 1,
    subchapters: [
      { id: 102, chapter_id: 11, subchapter_number: 1, title: "Stay Calm", content: "C" },
    ],
    quiz: null,
  },
];

beforeEach(() => {
  courseApi.chapters.mockResolvedValue(STRUCTURE);
  courseBuilderApi.create.mockResolvedValue(COURSE);
  courseBuilderApi.update.mockResolvedValue(COURSE);
});

describe("editing an existing course", () => {
  it("loads the structure into the form", async () => {
    render(<CourseBuilder course={COURSE} onClose={() => {}} onSaved={() => {}} />);

    expect(await screen.findByDisplayValue("Before The Alarm")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Know Your Exits")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Stay Calm")).toBeInTheDocument();
  });

  it("sends every existing id back, so progress stays attached", async () => {
    // The whole point. The API matches chapters and lessons by id; without
    // these the save reads as "delete everything and create new rows", and
    // every student's completion history against this course is destroyed.
    const user = userEvent.setup();
    render(<CourseBuilder course={COURSE} onClose={() => {}} onSaved={() => {}} />);

    await screen.findByDisplayValue("Before The Alarm");
    await user.click(screen.getByRole("button", { name: "Save course" }));

    await waitFor(() => expect(courseBuilderApi.update).toHaveBeenCalled());

    const [courseId, payload] = courseBuilderApi.update.mock.calls[0];
    expect(courseId).toBe(2);
    expect(payload.chapters.map((c) => c.id)).toEqual([10, 11]);
    expect(payload.chapters[0].subchapters.map((s) => s.id)).toEqual([100, 101]);
    expect(payload.chapters[1].subchapters.map((s) => s.id)).toEqual([102]);
  });

  it("keeps the ids after a title is edited", async () => {
    const user = userEvent.setup();
    render(<CourseBuilder course={COURSE} onClose={() => {}} onSaved={() => {}} />);

    const lesson = await screen.findByDisplayValue("Know Your Exits");
    await user.clear(lesson);
    await user.type(lesson, "Know Your Exits, Revised");

    await user.click(screen.getByRole("button", { name: "Save course" }));

    await waitFor(() => expect(courseBuilderApi.update).toHaveBeenCalled());
    const [, payload] = courseBuilderApi.update.mock.calls[0];
    expect(payload.chapters[0].subchapters[0]).toMatchObject({
      id: 100,
      title: "Know Your Exits, Revised",
    });
  });

  it("a newly added chapter carries no id", async () => {
    const user = userEvent.setup();
    render(<CourseBuilder course={COURSE} onClose={() => {}} onSaved={() => {}} />);

    await screen.findByDisplayValue("Before The Alarm");
    await user.click(screen.getByRole("button", { name: "Add chapter" }));

    const titles = screen.getAllByPlaceholderText("Chapter title");
    await user.type(titles[titles.length - 1], "A Third Chapter");

    await user.click(screen.getByRole("button", { name: "Save course" }));

    await waitFor(() => expect(courseBuilderApi.update).toHaveBeenCalled());
    const [, payload] = courseBuilderApi.update.mock.calls[0];
    expect(payload.chapters.map((c) => c.id)).toEqual([10, 11, null]);
  });

  it("removing a chapter drops it from the payload", async () => {
    const user = userEvent.setup();
    render(<CourseBuilder course={COURSE} onClose={() => {}} onSaved={() => {}} />);

    await screen.findByDisplayValue("Before The Alarm");
    const removeButtons = screen.getAllByRole("button", { name: "Remove chapter" });
    await user.click(removeButtons[1]);

    await user.click(screen.getByRole("button", { name: "Save course" }));

    await waitFor(() => expect(courseBuilderApi.update).toHaveBeenCalled());
    const [, payload] = courseBuilderApi.update.mock.calls[0];
    expect(payload.chapters.map((c) => c.id)).toEqual([10]);
  });
});

describe("creating a course", () => {
  it("does not fetch a structure it does not have", () => {
    render(<CourseBuilder onClose={() => {}} onSaved={() => {}} />);

    expect(courseApi.chapters).not.toHaveBeenCalled();
  });

  it("sends null ids for everything", async () => {
    const user = userEvent.setup();
    render(<CourseBuilder onClose={() => {}} onSaved={() => {}} />);

    await user.type(
      screen.getByPlaceholderText("Diamond grading fundamentals"),
      "Brand New"
    );
    await user.type(screen.getByPlaceholderText("Chapter title"), "One");
    await user.type(screen.getByPlaceholderText("Subchapter 1 title"), "Lesson");

    await user.click(screen.getByRole("button", { name: "Save course" }));

    await waitFor(() => expect(courseBuilderApi.create).toHaveBeenCalled());
    const [payload] = courseBuilderApi.create.mock.calls[0];
    expect(payload.title).toBe("Brand New");
    expect(payload.chapters[0].id).toBeNull();
    expect(payload.chapters[0].subchapters[0].id).toBeNull();
  });

  it("cannot be saved without a title", async () => {
    render(<CourseBuilder onClose={() => {}} onSaved={() => {}} />);

    expect(screen.getByRole("button", { name: "Save course" })).toBeDisabled();
  });
});

describe("when saving fails", () => {
  it("shows the reason and stays open", async () => {
    const user = userEvent.setup();
    courseBuilderApi.update.mockRejectedValue(
      new Error("Chapter 99 is not part of this course")
    );
    const onSaved = vi.fn();

    render(<CourseBuilder course={COURSE} onClose={() => {}} onSaved={onSaved} />);

    await screen.findByDisplayValue("Before The Alarm");
    await user.click(screen.getByRole("button", { name: "Save course" }));

    expect(
      await screen.findByText("Chapter 99 is not part of this course")
    ).toBeInTheDocument();
    expect(onSaved).not.toHaveBeenCalled();
  });
});
