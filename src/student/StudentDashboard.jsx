import { useNavigate } from "react-router-dom";
import { meApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import { useAuth } from "../auth/AuthContext";
import {
  Button,
  EmptyState,
  ErrorPanel,
  Loading,
  PageTitle,
  ProgressBar,
} from "../components/ui";

export default function StudentDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data, loading, error, reload } = useAsync(() => meApi.dashboard(), []);

  if (loading) return <Loading label="Loading your learning" />;

  if (error) {
    return (
      <>
        <PageTitle eyebrow="Your learning" title="My learning" />
        <ErrorPanel error={error} onRetry={reload} />
      </>
    );
  }

  const courses = data.courses || [];
  const inProgress = courses.filter((c) => c.progress > 0 && c.progress < 100);
  const notStarted = courses.filter((c) => c.progress === 0);
  const finished = courses.filter((c) => c.progress >= 100);

  const firstName = (data.name || "").split(" ")[0];

  return (
    <>
      <PageTitle
        eyebrow="Your learning"
        title={firstName ? `Welcome back, ${firstName}` : "My learning"}
        lede="Pick up where you left off, or begin something new from your assigned courses."
      />

      {courses.length === 0 ? (
        <EmptyState
          title="Nothing assigned yet"
          body={
            user?.department
              ? "No courses have been opened to your department and seniority yet. Your administrator will assign them."
              : "Your access profile has not been set. Ask your administrator to assign your department and seniority."
          }
        />
      ) : (
        <>
          <div className="stat-grid stat-grid-three">
            <div className="stat-card">
              <div className="stat-value">{inProgress.length}</div>
              <div className="stat-label">In progress</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{finished.length}</div>
              <div className="stat-label">Completed</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{notStarted.length}</div>
              <div className="stat-label">Not started</div>
            </div>
          </div>

          {inProgress.length > 0 && (
            <>
              <div className="section-heading">
                <h2 className="section-title">Continue</h2>
              </div>
              <div className="learn-list">
                {inProgress.map((course) => (
                  <article className="learn-card learn-card-feature" key={course.id}>
                    <div className="learn-card-body">
                      <h3 className="learn-card-title">{course.title}</h3>
                      {course.next_subchapter && (
                        <div className="learn-card-next">
                          Up next — {course.next_subchapter}
                        </div>
                      )}
                      <div className="learn-card-progress">
                        <ProgressBar value={course.progress} wide />
                        <span className="table-progress-num">{Math.round(course.progress)}%</span>
                      </div>
                    </div>
                    <Button onClick={() => navigate(`/courses/${course.id}`)}>Continue</Button>
                  </article>
                ))}
              </div>
            </>
          )}

          {notStarted.length > 0 && (
            <>
              <div className="section-heading">
                <h2 className="section-title">Begin</h2>
              </div>
              <div className="learn-list">
                {notStarted.map((course) => (
                  <article className="learn-card" key={course.id}>
                    <div className="learn-card-body">
                      <h3 className="learn-card-title">{course.title}</h3>
                      {course.next_subchapter && (
                        <div className="learn-card-next">Starts with {course.next_subchapter}</div>
                      )}
                    </div>
                    <Button variant="ghost" onClick={() => navigate(`/courses/${course.id}`)}>
                      Start
                    </Button>
                  </article>
                ))}
              </div>
            </>
          )}

          {finished.length > 0 && (
            <>
              <div className="section-heading">
                <h2 className="section-title">Completed</h2>
              </div>
              <div className="learn-list">
                {finished.map((course) => (
                  <article className="learn-card learn-card-done" key={course.id}>
                    <div className="learn-card-body">
                      <h3 className="learn-card-title">{course.title}</h3>
                      <div className="learn-card-next">Every subchapter complete</div>
                    </div>
                    <Button variant="ghost" onClick={() => navigate(`/courses/${course.id}`)}>
                      Revisit
                    </Button>
                  </article>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </>
  );
}
