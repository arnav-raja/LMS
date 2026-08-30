import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import QuizTake from "./QuizTake";
import { quizApi } from "../api/endpoints";
import { renderAt } from "../test/render";

vi.mock("../api/endpoints", () => ({
  quizApi: {
    take: vi.fn(),
    submit: vi.fn(),
  },
}));

const QUIZ = {
  id: 7,
  chapter_id: 3,
  course_id: 2,
  title: "Fire Safety Check",
  passing_score: 70,
  questions: [
    {
      id: 11,
      question_number: 1,
      question_text: "Where is the nearest exit?",
      options: [
        { id: 101, option_text: "Down the hall" },
        { id: 102, option_text: "Through the window" },
      ],
    },
    {
      id: 12,
      question_number: 2,
      question_text: "Who do you report to?",
      options: [
        { id: 103, option_text: "The fire warden" },
        { id: 104, option_text: "Nobody" },
      ],
    },
  ],
};

function renderQuiz() {
  return renderAt(<QuizTake />, {
    path: "/quizzes/:quizId",
    at: "/quizzes/7",
  });
}

async function answerEverything(user) {
  await user.click(await screen.findByLabelText("Down the hall"));
  await user.click(screen.getByLabelText("The fire warden"));
}

beforeEach(() => {
  quizApi.take.mockResolvedValue(QUIZ);
  quizApi.submit.mockReset();
});

describe("taking a quiz", () => {
  it("shows every question and its options", async () => {
    renderQuiz();

    expect(await screen.findByText("Fire Safety Check")).toBeInTheDocument();
    expect(screen.getByText("Where is the nearest exit?")).toBeInTheDocument();
    expect(screen.getByText("Who do you report to?")).toBeInTheDocument();
    expect(screen.getByLabelText("Down the hall")).toBeInTheDocument();
  });

  it("cannot be submitted until every question is answered", async () => {
    const user = userEvent.setup();
    renderQuiz();

    const submit = await screen.findByRole("button", { name: "Submit quiz" });
    expect(submit).toBeDisabled();

    await user.click(screen.getByLabelText("Down the hall"));
    expect(submit).toBeDisabled();

    await user.click(screen.getByLabelText("The fire warden"));
    expect(submit).toBeEnabled();
  });

  it("counts how many are answered", async () => {
    const user = userEvent.setup();
    renderQuiz();

    expect(await screen.findByText("0 of 2 answered")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Down the hall"));
    expect(screen.getByText("1 of 2 answered")).toBeInTheDocument();
  });

  it("sends the selected option for each question", async () => {
    const user = userEvent.setup();
    quizApi.submit.mockResolvedValue({ passed: false, score: 50, course_id: 2 });
    renderQuiz();

    await answerEverything(user);
    await user.click(screen.getByRole("button", { name: "Submit quiz" }));

    await waitFor(() => expect(quizApi.submit).toHaveBeenCalled());
    expect(quizApi.submit).toHaveBeenCalledWith("7", [
      { question_id: 11, option_id: 101 },
      { question_id: 12, option_id: 103 },
    ]);
  });

  it("changing an answer replaces it rather than adding one", async () => {
    const user = userEvent.setup();
    quizApi.submit.mockResolvedValue({ passed: false, score: 0, course_id: 2 });
    renderQuiz();

    await user.click(await screen.findByLabelText("Down the hall"));
    await user.click(screen.getByLabelText("Through the window"));
    await user.click(screen.getByLabelText("The fire warden"));

    await user.click(screen.getByRole("button", { name: "Submit quiz" }));

    await waitFor(() => expect(quizApi.submit).toHaveBeenCalled());
    expect(quizApi.submit.mock.calls[0][1][0]).toEqual({
      question_id: 11,
      option_id: 102,
    });
  });
});

describe("after submitting", () => {
  it("passing returns the student to the course, not the quiz list", async () => {
    const user = userEvent.setup();
    quizApi.submit.mockResolvedValue({
      passed: true,
      score: 100,
      course_id: 2,
      certificate_issued: false,
    });

    const view = renderQuiz();
    await answerEverything(user);
    await user.click(screen.getByRole("button", { name: "Submit quiz" }));

    await waitFor(() => expect(view.navigatedTo()).toBe("/courses/2"));
  });

  it("a pass that finishes the course flags the certificate hand-off", async () => {
    const user = userEvent.setup();
    quizApi.submit.mockResolvedValue({
      passed: true,
      score: 100,
      course_id: 2,
      certificate_issued: true,
    });

    const view = renderQuiz();
    await answerEverything(user);
    await user.click(screen.getByRole("button", { name: "Submit quiz" }));

    await waitFor(() =>
      expect(view.navigatedState()).toEqual({ showCertificateInterstitial: true })
    );
  });

  it("failing stays put and offers a retake", async () => {
    const user = userEvent.setup();
    quizApi.submit.mockResolvedValue({ passed: false, score: 50, course_id: 2 });

    renderQuiz();
    await answerEverything(user);
    await user.click(screen.getByRole("button", { name: "Submit quiz" }));

    expect(await screen.findByText("Not quite there")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retake now" })).toBeInTheDocument();
  });

  it("retaking clears the previous answers", async () => {
    const user = userEvent.setup();
    quizApi.submit.mockResolvedValue({ passed: false, score: 50, course_id: 2 });

    renderQuiz();
    await answerEverything(user);
    await user.click(screen.getByRole("button", { name: "Submit quiz" }));

    await user.click(await screen.findByRole("button", { name: "Retake now" }));

    expect(await screen.findByText("0 of 2 answered")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit quiz" })).toBeDisabled();
  });

  it("shows the reason a submission was rejected", async () => {
    const user = userEvent.setup();
    quizApi.submit.mockRejectedValue(
      Object.assign(new Error("Complete every lesson in this chapter first"), {
        status: 403,
      })
    );

    renderQuiz();
    await answerEverything(user);
    await user.click(screen.getByRole("button", { name: "Submit quiz" }));

    expect(
      await screen.findByText("Complete every lesson in this chapter first")
    ).toBeInTheDocument();
  });
});

describe("when the quiz cannot be opened", () => {
  it("explains rather than showing an empty page", async () => {
    quizApi.take.mockRejectedValue(
      Object.assign(new Error("Complete every lesson in this chapter first"), {
        status: 403,
        isForbidden: true,
      })
    );

    renderQuiz();

    expect(
      await screen.findByText("Could not open this quiz")
    ).toBeInTheDocument();
  });
});
