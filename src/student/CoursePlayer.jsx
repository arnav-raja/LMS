import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { PanelLeftClose, PanelLeftOpen, ChevronDown, ChevronRight, ClipboardList, CheckCircle2, Lock } from "lucide-react";
import { courseApi, learningApi, progressApi } from "../api/endpoints";
import { Button, ErrorPanel, Loading, ProgressBar } from "../components/ui";

const RAIL_OPEN_KEY = "arnav.playerRailOpen";

export default function CoursePlayer() {
  const { courseId } = useParams();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [progress, setProgress] = useState(null);
  const [activeId, setActiveId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [completing, setCompleting] = useState(false);
  const [actionError, setActionError] = useState(null);

  // The rail can be hidden entirely to give lesson text the full width —
  // remembered across visits, same as the sidebar's collapse state.
  const [railOpen, setRailOpen] = useState(() => {
    try {
      const stored = window.localStorage.getItem(RAIL_OPEN_KEY);
      return stored === null ? true : stored === "true";
    } catch {
      return true;
    }
  });

  // Accordion: only one chapter's subchapter list is expanded at a time,
  // so the rail shows structure without listing every lesson in the course
  // at once. Defaults to whichever chapter contains the active lesson.
  const [expandedChapterId, setExpandedChapterId] = useState(null);

  const toggleRail = () => {
    setRailOpen((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(RAIL_OPEN_KEY, String(next));
      } catch {
        /* preference just won't persist */
      }
      return next;
    });
  };

  /** Pulls the course structure, progress figures, and the resume point. */
  const load = useCallback(
    async ({ keepActive = false } = {}) => {
      setError(null);
      try {
        const [courseList, chapterData, progressData] = await Promise.all([
          courseApi.list(),
          courseApi.chapters(courseId),
          learningApi.progress(courseId),
        ]);

        setCourse(courseList.find((c) => String(c.id) === String(courseId)) || null);
        setChapters(chapterData);
        setProgress(progressData);

        if (!keepActive) {
          // The continue endpoint answers 404 once everything is done —
          // that is a finished course, not a failure.
          let resumeId = null;
          try {
            const resume = await learningApi.continueCourse(courseId);
            resumeId = resume.subchapter_id;
          } catch (err) {
            if (!err.isNotFound) throw err;
          }

          const firstUnlocked = chapterData
            .flatMap((c) => c.subchapters)
            .find((s) => !s.is_locked);

          const nextActiveId = resumeId || firstUnlocked?.id || null;
          setActiveId(nextActiveId);

          const owningChapter = chapterData.find((c) =>
            c.subchapters.some((s) => s.id === nextActiveId)
          );
          setExpandedChapterId(owningChapter?.id ?? chapterData[0]?.id ?? null);
        }
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    },
    [courseId]
  );

  useEffect(() => {
    load();
  }, [load]);

  const allSubchapters = useMemo(
    () =>
      chapters.flatMap((chapter) =>
        chapter.subchapters.map((sub) => ({ ...sub, chapter }))
      ),
    [chapters]
  );

  const active = allSubchapters.find((s) => s.id === activeId) || null;
  const activeIndex = allSubchapters.findIndex((s) => s.id === activeId);
  const next = activeIndex >= 0 ? allSubchapters[activeIndex + 1] : null;

  const selectLesson = (subchapter, chapterId) => {
    if (subchapter.is_locked) return;
    setActiveId(subchapter.id);
    setExpandedChapterId(chapterId);
  };

  const markComplete = async () => {
    if (!active) return;
    setCompleting(true);
    setActionError(null);
    try {
      await progressApi.complete(active.id);
      await load({ keepActive: true });
      // Move forward once the next lesson has unlocked.
      if (next) {
        setActiveId(next.id);
        setExpandedChapterId(next.chapter.id);
      }
    } catch (err) {
      setActionError(err.message);
    } finally {
      setCompleting(false);
    }
  };

  if (loading) return <Loading label="Opening course" />;

  if (error) {
    return (
      <>
        <button className="back-link" onClick={() => navigate("/courses")}>
          Back to courses
        </button>
        <h1 className="page-title">Could not open this course</h1>
        <ErrorPanel error={error} onRetry={() => load()} />
      </>
    );
  }

  const percentage = progress?.percentage ?? 0;
  const finished = percentage >= 100;

  return (
    <div className="player">
      <button className="back-link" onClick={() => navigate("/courses")}>
        Back to courses
      </button>

      <header className="player-header">
        <div>
          <div className="eyebrow">Course</div>
          <h1 className="page-title">{course?.title || "Course"}</h1>
        </div>
        <div className="player-progress">
          <ProgressBar value={percentage} wide />
          <div className="player-progress-meta">
            {progress?.completed_subchapters ?? 0} of {progress?.total_subchapters ?? 0} lessons
            complete
          </div>
        </div>
      </header>

      {finished && (
        <div className="player-banner">
          You have completed every lesson in this course. Revisit any lesson below at any time.
        </div>
      )}

      <button
        className="player-rail-toggle"
        onClick={toggleRail}
        aria-expanded={railOpen}
      >
        {railOpen ? <PanelLeftClose size={15} /> : <PanelLeftOpen size={15} />}
        {railOpen ? "Hide contents" : "Show contents"}
      </button>

      <div className={`player-body ${railOpen ? "" : "player-body-rail-closed"}`}>
        {railOpen && (
          <nav className="player-rail" aria-label="Course contents">
            {chapters.map((chapter) => {
              const isExpanded = chapter.id === expandedChapterId;
              const completedCount = chapter.subchapters.filter((s) => s.is_completed).length;

              return (
                <div className="rail-chapter" key={chapter.id}>
                  <button
                    className="rail-chapter-header"
                    onClick={() =>
                      setExpandedChapterId(isExpanded ? null : chapter.id)
                    }
                    aria-expanded={isExpanded}
                  >
                    {isExpanded ? (
                      <ChevronDown size={14} className="rail-chapter-chevron" />
                    ) : (
                      <ChevronRight size={14} className="rail-chapter-chevron" />
                    )}
                    <span className="rail-chapter-number">{chapter.chapter_number}</span>
                    <span className="rail-chapter-title-text">{chapter.title}</span>
                    <span className="rail-chapter-count">
                      {completedCount}/{chapter.subchapters.length}
                    </span>
                  </button>

                  {isExpanded && (
                    <ul className="rail-list">
                      {chapter.subchapters.map((sub) => {
                        const state = sub.is_completed
                          ? "done"
                          : sub.is_locked
                          ? "locked"
                          : "open";
                        const isActive = sub.id === activeId;
                        return (
                          <li key={sub.id}>
                            <button
                              className={`rail-item rail-item-${state} ${
                                isActive ? "rail-item-active" : ""
                              }`}
                              onClick={() => selectLesson(sub, chapter.id)}
                              disabled={sub.is_locked}
                              title={
                                sub.is_locked
                                  ? "Complete the previous lesson first"
                                  : undefined
                              }
                            >
                              <span className="chapter-dot" />
                              <span className="rail-item-title">{sub.title}</span>
                            </button>
                          </li>
                        );
                      })}

                      {chapter.quiz && (
                        <li>
                          <button
                            className={`rail-item rail-item-${
                              chapter.quiz.is_passed
                                ? "done"
                                : chapter.quiz.is_unlocked
                                ? "open"
                                : "locked"
                            }`}
                            onClick={() =>
                              chapter.quiz.is_unlocked && navigate(`/quizzes/${chapter.quiz.id}`)
                            }
                            disabled={!chapter.quiz.is_unlocked}
                            title={
                              !chapter.quiz.is_unlocked
                                ? "Complete every lesson in this chapter first"
                                : "Mandatory quiz for this chapter"
                            }
                          >
                            {chapter.quiz.is_passed ? (
                              <CheckCircle2 size={14} className="chapter-dot" />
                            ) : chapter.quiz.is_unlocked ? (
                              <ClipboardList size={14} className="chapter-dot" />
                            ) : (
                              <Lock size={14} className="chapter-dot" />
                            )}
                            <span className="rail-item-title">
                              {chapter.quiz.title}
                              {chapter.quiz.is_passed
                                ? " — passed"
                                : chapter.quiz.attempts_count > 0
                                ? " — retake"
                                : ""}
                            </span>
                          </button>
                        </li>
                      )}
                    </ul>
                  )}
                </div>
              );
            })}
          </nav>
        )}

        <section className="player-content">
          {!active ? (
            <div className="player-placeholder">
              Select a lesson from the contents to begin.
            </div>
          ) : (
            <>
              <div className="lesson-eyebrow">
                Chapter {active.chapter.chapter_number} · Lesson {active.subchapter_number}
              </div>
              <h2 className="lesson-title">{active.title}</h2>

              <div className="lesson-body">
                {active.content ? (
                  active.content.split(/\n{2,}/).map((paragraph, i) => (
                    <p key={i}>{paragraph}</p>
                  ))
                ) : (
                  <p className="muted">This lesson has no written content yet.</p>
                )}
              </div>

              {actionError && <div className="form-error">{actionError}</div>}

              <div className="lesson-actions">
                {active.is_completed ? (
                  <>
                    <span className="lesson-done-mark">Completed</span>
                    {next && !next.is_locked && (
                      <Button
                        variant="ghost"
                        onClick={() => {
                          setActiveId(next.id);
                          setExpandedChapterId(next.chapter.id);
                        }}
                      >
                        Next lesson
                      </Button>
                    )}
                  </>
                ) : (
                  <Button onClick={markComplete} disabled={completing}>
                    {completing ? "Saving" : "Mark complete"}
                  </Button>
                )}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
