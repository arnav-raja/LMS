import { useNavigate } from "react-router-dom";
import { quizApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import { EmptyState, ErrorPanel, Loading, PageTitle, StatusBadge } from "../components/ui";

const STATUS_LABEL = {
  locked: "Locked",
  available: "Available",
  passed: "Passed",
  failed: "Retake",
};

const STATUS_BADGE = {
  locked: "draft",
  available: "draft",
  passed: "published",
  failed: "archived",
};

export default function StudentQuizzes() {
  const navigate = useNavigate();
  const { data: quizzes, loading, error, reload } = useAsync(() => quizApi.mine(), []);

  if (loading) return <Loading label="Loading your quizzes" />;
  if (error) return <ErrorPanel error={error} onRetry={reload} />;

  return (
    <>
      <PageTitle
        eyebrow="Quizzes"
        title="Your quizzes"
        lede="Every chapter ends with a short quiz. Passing it is mandatory before the next chapter unlocks."
      />

      {quizzes.length === 0 ? (
        <EmptyState
          title="No quizzes available yet"
          body="Quizzes will appear here as you make your way through your courses."
        />
      ) : (
        <div className="table-card">
          <table className="table">
            <thead>
              <tr>
                <th>Course</th>
                <th>Chapter</th>
                <th>Quiz</th>
                <th>Questions</th>
                <th>Best score</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {quizzes.map((quiz) => {
                const clickable = quiz.status !== "locked";
                return (
                  <tr
                    key={quiz.quiz_id}
                    className={clickable ? "table-row-clickable" : ""}
                    onClick={() => clickable && navigate(`/quizzes/${quiz.quiz_id}`)}
                  >
                    <td>{quiz.course_title}</td>
                    <td>{quiz.chapter_title}</td>
                    <td className="table-title-cell">{quiz.quiz_title}</td>
                    <td>{quiz.question_count}</td>
                    <td>
                      {quiz.best_score !== null && quiz.best_score !== undefined
                        ? `${quiz.best_score}%`
                        : <span className="muted">—</span>}
                    </td>
                    <td>
                      <StatusBadge status={STATUS_BADGE[quiz.status]} />
                      <span style={{ marginLeft: 8 }}>{STATUS_LABEL[quiz.status]}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
