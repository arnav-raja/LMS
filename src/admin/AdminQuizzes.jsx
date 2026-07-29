import { useEffect, useState } from "react";
import { courseApi, quizApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import {
  Button,
  Drawer,
  EmptyState,
  ErrorPanel,
  Loading,
  Modal,
  PageTitle,
} from "../components/ui";

const blankOption = () => ({ option_text: "", is_correct: false });
const blankQuestion = () => ({ question_text: "", options: [blankOption(), blankOption()] });

/** Builder for a single chapter's quiz — one course/chapter picked first,
 * then MCQ questions authored below with the correct option marked. */
function QuizBuilder({ chapters, existingQuiz, defaultChapterId, onClose, onSaved }) {
  const [chapterId, setChapterId] = useState(
    existingQuiz?.chapter_id || defaultChapterId || chapters[0]?.id || ""
  );
  const [title, setTitle] = useState(existingQuiz?.title || "");
  const [passingScore, setPassingScore] = useState(existingQuiz?.passing_score ?? 70);
  const [questions, setQuestions] = useState(
    existingQuiz?.questions?.length
      ? existingQuiz.questions.map((q) => ({
          question_text: q.question_text,
          options: q.options.map((o) => ({
            option_text: o.option_text,
            is_correct: o.is_correct,
          })),
        }))
      : [blankQuestion()]
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const editing = Boolean(existingQuiz);

  const updateQuestion = (index, patch) =>
    setQuestions(questions.map((q, i) => (i === index ? { ...q, ...patch } : q)));

  const updateOption = (qIndex, oIndex, patch) =>
    setQuestions(
      questions.map((q, i) =>
        i === qIndex
          ? { ...q, options: q.options.map((o, j) => (j === oIndex ? { ...o, ...patch } : o)) }
          : q
      )
    );

  const setCorrectOption = (qIndex, oIndex) =>
    setQuestions(
      questions.map((q, i) =>
        i === qIndex
          ? { ...q, options: q.options.map((o, j) => ({ ...o, is_correct: j === oIndex })) }
          : q
      )
    );

  const addQuestion = () => setQuestions([...questions, blankQuestion()]);
  const removeQuestion = (index) => setQuestions(questions.filter((_, i) => i !== index));

  const addOption = (qIndex) =>
    setQuestions(
      questions.map((q, i) => (i === qIndex ? { ...q, options: [...q.options, blankOption()] } : q))
    );

  const removeOption = (qIndex, oIndex) =>
    setQuestions(
      questions.map((q, i) =>
        i === qIndex ? { ...q, options: q.options.filter((_, j) => j !== oIndex) } : q
      )
    );

  const isValid =
    chapterId &&
    title.trim() &&
    questions.length > 0 &&
    questions.every(
      (q) =>
        q.question_text.trim() &&
        q.options.filter((o) => o.option_text.trim()).length >= 2 &&
        q.options.some((o) => o.is_correct && o.option_text.trim())
    );

  const save = async () => {
    setSaving(true);
    setError(null);

    const payload = {
      title: title.trim(),
      passing_score: Number(passingScore) || 70,
      questions: questions.map((q) => ({
        question_text: q.question_text.trim(),
        options: q.options
          .filter((o) => o.option_text.trim())
          .map((o) => ({ option_text: o.option_text.trim(), is_correct: o.is_correct })),
      })),
    };

    try {
      await quizApi.save(chapterId, payload);
      onSaved();
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  return (
    <Modal
      wide
      eyebrow={editing ? "Edit quiz" : "New quiz"}
      title={editing ? existingQuiz.title : "Build a chapter quiz"}
      onClose={onClose}
      actions={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={save} disabled={saving || !isValid}>
            {saving ? "Saving" : "Save quiz"}
          </Button>
        </>
      }
    >
      {error && <ErrorPanel error={error} />}

      <label className="field-label" htmlFor="quiz-chapter">
        Chapter
      </label>
      <select
        id="quiz-chapter"
        className="text-input"
        value={chapterId}
        onChange={(e) => setChapterId(Number(e.target.value))}
        disabled={editing}
      >
        {chapters.map((chapter) => (
          <option key={chapter.id} value={chapter.id}>
            {chapter.courseTitle} — Chapter {chapter.chapter_number}: {chapter.title}
          </option>
        ))}
      </select>

      <label className="field-label" htmlFor="quiz-title">
        Quiz title
      </label>
      <input
        id="quiz-title"
        className="text-input"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="e.g. Chapter 1 checkpoint"
      />

      <label className="field-label" htmlFor="quiz-passing-score">
        Passing score (%)
      </label>
      <input
        id="quiz-passing-score"
        className="text-input"
        type="number"
        min="0"
        max="100"
        value={passingScore}
        onChange={(e) => setPassingScore(e.target.value)}
      />

      <div className="builder-heading">Questions</div>

      {questions.map((question, qIndex) => (
        <div className="builder-chapter" key={qIndex}>
          <div className="builder-chapter-head">
            <span className="builder-chapter-number">{qIndex + 1}</span>
            <input
              className="text-input"
              value={question.question_text}
              onChange={(e) => updateQuestion(qIndex, { question_text: e.target.value })}
              placeholder="Question text"
            />
            {questions.length > 1 && (
              <button
                type="button"
                className="btn-icon btn-icon-danger"
                onClick={() => removeQuestion(qIndex)}
                title="Remove question"
              >
                ✕
              </button>
            )}
          </div>

          {question.options.map((option, oIndex) => (
            <div className="builder-sub" key={oIndex}>
              <input
                type="radio"
                name={`correct-${qIndex}`}
                checked={option.is_correct}
                onChange={() => setCorrectOption(qIndex, oIndex)}
                title="Mark as the correct answer"
              />
              <input
                className="text-input"
                value={option.option_text}
                onChange={(e) => updateOption(qIndex, oIndex, { option_text: e.target.value })}
                placeholder={`Option ${oIndex + 1}`}
              />
              {question.options.length > 2 && (
                <button
                  type="button"
                  className="btn-icon btn-icon-danger"
                  onClick={() => removeOption(qIndex, oIndex)}
                  title="Remove option"
                >
                  ✕
                </button>
              )}
            </div>
          ))}

          {question.options.length < 4 && (
            <Button variant="ghost" onClick={() => addOption(qIndex)}>
              Add option
            </Button>
          )}
        </div>
      ))}

      <Button variant="ghost" onClick={addQuestion}>
        Add question
      </Button>
    </Modal>
  );
}

export default function AdminQuizzes() {
  const { data: quizzes, loading, error, reload } = useAsync(() => quizApi.adminList(), []);

  const [courses, setCourses] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [builderOpen, setBuilderOpen] = useState(false);
  const [editingQuiz, setEditingQuiz] = useState(null);
  const [defaultChapterId, setDefaultChapterId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [results, setResults] = useState(null);
  const [resultsLoading, setResultsLoading] = useState(false);

  // The builder needs every chapter across every course, flattened, so an
  // admin can pick "which chapter is this quiz for" from one list.
  useEffect(() => {
    let cancelled = false;

    courseApi
      .list()
      .then(async (courseList) => {
        if (cancelled) return;
        setCourses(courseList);

        const chapterLists = await Promise.all(
          courseList.map((course) =>
            courseApi
              .chapters(course.id)
              .then((chs) => chs.map((c) => ({ ...c, courseTitle: course.title })))
          )
        );

        if (!cancelled) setChapters(chapterLists.flat());
      })
      .catch(() => {
        /* the quizzes list itself will surface a load error already */
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const openNewQuiz = () => {
    setEditingQuiz(null);
    setDefaultChapterId(chapters.find((c) => !c.quiz)?.id ?? chapters[0]?.id ?? null);
    setBuilderOpen(true);
  };

  const openEditQuiz = async (quizId) => {
    const full = await quizApi.adminGet(quizId);
    setEditingQuiz(full);
    setBuilderOpen(true);
  };

  const viewResults = async (quizId) => {
    setResultsLoading(true);
    try {
      const data = await quizApi.results(quizId);
      setResults(data);
    } finally {
      setResultsLoading(false);
    }
  };

  const removeQuiz = async (quizId) => {
    setDeletingId(quizId);
    try {
      await quizApi.remove(quizId);
      reload();
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <Loading label="Loading quizzes" />;
  if (error) return <ErrorPanel error={error} onRetry={reload} />;

  return (
    <>
      <PageTitle
        eyebrow="Quizzes"
        title="Chapter quizzes"
        lede="Every chapter has one mandatory multiple-choice quiz. A student cannot move to the next chapter until they pass it."
        action={
          <Button onClick={openNewQuiz} disabled={chapters.length === 0}>
            New quiz
          </Button>
        }
      />

      {quizzes.length === 0 ? (
        <EmptyState
          title="No quizzes yet"
          body="Create your first course chapter, then come back here to add its quiz."
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
                <th>Pass mark</th>
                <th>Attempts</th>
                <th>Pass rate</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {quizzes.map((quiz) => (
                <tr key={quiz.quiz_id}>
                  <td>{quiz.course_title}</td>
                  <td>{quiz.chapter_title}</td>
                  <td className="table-title-cell">{quiz.quiz_title}</td>
                  <td>{quiz.question_count}</td>
                  <td>{quiz.passing_score}%</td>
                  <td>{quiz.attempts_count}</td>
                  <td>
                    {quiz.attempts_count > 0
                      ? `${Math.round((quiz.pass_count / quiz.attempts_count) * 100)}%`
                      : <span className="muted">No attempts</span>}
                  </td>
                  <td className="table-action-cell">
                    <button
                      className="btn-icon-quiet"
                      onClick={() => viewResults(quiz.quiz_id)}
                      title="View results"
                    >
                      Results
                    </button>
                    <button
                      className="btn-icon-quiet"
                      onClick={() => openEditQuiz(quiz.quiz_id)}
                      title="Edit quiz"
                    >
                      Edit
                    </button>
                    <button
                      className="btn-icon btn-icon-danger"
                      onClick={() => removeQuiz(quiz.quiz_id)}
                      disabled={deletingId === quiz.quiz_id}
                      title="Delete quiz"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {builderOpen && chapters.length > 0 && (
        <QuizBuilder
          chapters={chapters}
          existingQuiz={editingQuiz}
          defaultChapterId={defaultChapterId}
          onClose={() => setBuilderOpen(false)}
          onSaved={() => {
            setBuilderOpen(false);
            reload();
          }}
        />
      )}

      {(results || resultsLoading) && (
        <Drawer
          eyebrow="Results"
          title={results?.quiz_title || "Loading"}
          onClose={() => setResults(null)}
        >
          {resultsLoading ? (
            <Loading label="Loading results" />
          ) : results.rows.length === 0 ? (
            <p className="muted">No one has attempted this quiz yet.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Attempts</th>
                  <th>Best score</th>
                  <th>Passed</th>
                </tr>
              </thead>
              <tbody>
                {results.rows.map((row) => (
                  <tr key={row.user_id}>
                    <td className="table-title-cell">{row.user_name}</td>
                    <td>{row.attempts_count}</td>
                    <td>{row.best_score}%</td>
                    <td>{row.passed ? "Yes" : "Not yet"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Drawer>
      )}
    </>
  );
}
