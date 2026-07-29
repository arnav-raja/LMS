import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { quizApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import { Button, ErrorPanel, Loading } from "../components/ui";

export default function QuizTake() {
  const { quizId } = useParams();
  const navigate = useNavigate();

  const { data: quiz, loading, error } = useAsync(() => quizApi.take(quizId), [quizId]);

  const [selections, setSelections] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [result, setResult] = useState(null);

  if (loading) return <Loading label="Loading quiz" />;

  if (error) {
    return (
      <>
        <button className="back-link" onClick={() => navigate("/quizzes")}>
          Back to quizzes
        </button>
        <h1 className="page-title">Could not open this quiz</h1>
        <ErrorPanel error={error} />
      </>
    );
  }

  const selectOption = (questionId, optionId) =>
    setSelections((prev) => ({ ...prev, [questionId]: optionId }));

  const allAnswered = quiz.questions.every((q) => selections[q.id] !== undefined);

  const submit = async () => {
    setSubmitting(true);
    setSubmitError(null);

    const answers = quiz.questions.map((q) => ({
      question_id: q.id,
      option_id: selections[q.id] ?? null,
    }));

    try {
      const attempt = await quizApi.submit(quizId, answers);
      setResult(attempt);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <>
        <button className="back-link" onClick={() => navigate("/quizzes")}>
          Back to quizzes
        </button>

        <h1 className="page-title">{result.passed ? "You passed" : "Not quite there"}</h1>

        <div className="player-banner">
          You scored <strong>{result.score}%</strong> — the pass mark is {quiz.passing_score}%.
          {result.passed
            ? " The next chapter is now unlocked."
            : " Review the chapter's lessons and try again when you're ready."}
        </div>

        <div className="lesson-actions">
          <Button onClick={() => navigate("/quizzes")}>Back to quizzes</Button>
          {!result.passed && (
            <Button
              variant="ghost"
              onClick={() => {
                setResult(null);
                setSelections({});
              }}
            >
              Retake now
            </Button>
          )}
        </div>
      </>
    );
  }

  return (
    <>
      <button className="back-link" onClick={() => navigate("/quizzes")}>
        Back to quizzes
      </button>

      <div className="eyebrow">Quiz</div>
      <h1 className="page-title">{quiz.title}</h1>
      <p className="page-lede">
        Answer every question, then submit. You need {quiz.passing_score}% to pass.
      </p>

      {quiz.questions.map((question, index) => (
        <div className="builder-chapter" key={question.id}>
          <div className="builder-chapter-head">
            <span className="builder-chapter-number">{index + 1}</span>
            <span className="lesson-title" style={{ fontSize: "1rem" }}>
              {question.question_text}
            </span>
          </div>

          {question.options.map((option) => (
            <label className="builder-sub" key={option.id} style={{ cursor: "pointer" }}>
              <input
                type="radio"
                name={`question-${question.id}`}
                checked={selections[question.id] === option.id}
                onChange={() => selectOption(question.id, option.id)}
              />
              <span>{option.option_text}</span>
            </label>
          ))}
        </div>
      ))}

      {submitError && <div className="form-error">{submitError}</div>}

      <div className="lesson-actions">
        <Button onClick={submit} disabled={!allAnswered || submitting}>
          {submitting ? "Submitting" : "Submit quiz"}
        </Button>
      </div>
    </>
  );
}
