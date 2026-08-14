import { useNavigate } from "react-router-dom";
import { courseApi, meApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import {
  Button,
  EmptyState,
  ErrorPanel,
  Loading,
  PageTitle,
  ProgressBar,
} from "../components/ui";

export default function StudentCourses() {
  const navigate = useNavigate();
  const courses = useAsync(() => courseApi.list(), []);
  const dashboard = useAsync(() => meApi.dashboard(), []);

  if (courses.loading || dashboard.loading) return <Loading label="Loading courses" />;

  const error = courses.error || dashboard.error;
  if (error) {
    return (
      <>
        <PageTitle eyebrow="Catalogue" title="Courses" />
        <ErrorPanel
          error={error}
          onRetry={() => {
            courses.reload();
            dashboard.reload();
          }}
        />
      </>
    );
  }

  const progressById = new Map(
    (dashboard.data?.courses || []).map((c) => [c.id, c])
  );
  const list = courses.data || [];

  return (
    <>
      <PageTitle
        eyebrow="Catalogue"
        title="Courses"
        lede="Everything open to your department and seniority."
      />

      {list.length === 0 ? (
        <EmptyState
          title="No courses available"
          body="Nothing has been opened to your department and seniority yet. Your administrator will assign courses when they are ready."
        />
      ) : (
        <div className="course-grid">
          {list.map((course) => {
            const progress = progressById.get(course.id);
            const pct = progress?.progress ?? 0;
            const started = pct > 0;
            const done = pct >= 100;

            return (
              <article className="course-card" key={course.id}>
                <div className="course-card-top">
                  <span className="course-card-chapters">
                    {course.num_chapters} {course.num_chapters === 1 ? "chapter" : "chapters"}
                  </span>
                  {done && <span className="badge badge-published">complete</span>}
                </div>

                <h3 className="course-card-title">{course.title}</h3>
                <p className="course-card-desc">{course.description}</p>

                {started && (
                  <div className="table-progress course-card-progress">
                    <ProgressBar value={pct} />
                    <span className="table-progress-num">{Math.round(pct)}%</span>
                  </div>
                )}

                {progress?.next_subchapter && !done && (
                  <div className="course-card-next">Up next — {progress.next_subchapter}</div>
                )}

                <div className="course-card-actions">
                  <Button
                    variant={started && !done ? "gold" : "ghost"}
                    onClick={() => navigate(`/courses/${course.id}`)}
                  >
                    {done ? "Revisit" : started ? "Continue" : "Start"}
                  </Button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}
