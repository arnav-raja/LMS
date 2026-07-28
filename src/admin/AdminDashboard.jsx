import { useNavigate } from "react-router-dom";
import { adminApi, courseApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import { ErrorPanel, Loading, PageTitle, StatCard, StatusBadge } from "../components/ui";

export default function AdminDashboard() {
  const navigate = useNavigate();

  const stats = useAsync(() => adminApi.dashboard(), []);
  const courses = useAsync(() => courseApi.list(), []);

  if (stats.loading || courses.loading) return <Loading label="Loading dashboard" />;

  const error = stats.error || courses.error;
  if (error) {
    return (
      <>
        <PageTitle eyebrow="Overview" title="Dashboard" />
        <ErrorPanel
          error={error}
          onRetry={() => {
            stats.reload();
            courses.reload();
          }}
        />
      </>
    );
  }

  const list = courses.data || [];
  const published = list.filter((c) => c.status === "published");
  const drafts = list.filter((c) => c.status === "draft");

  return (
    <>
      <PageTitle
        eyebrow="Overview"
        title="Dashboard"
        lede="A daily reading on the training floor — who is learning, and what still needs attention."
      />

      <div className="stat-grid">
        <StatCard
          label="Students"
          value={stats.data.total_students}
          footnote="View students →"
          onClick={() => navigate("/admin/students")}
        />
        <StatCard
          label="Courses"
          value={list.length}
          footnote={`${published.length} published — view courses →`}
          onClick={() => navigate("/admin/courses")}
        />
        <StatCard
          label="Students without access"
          value={stats.data.students_without_access}
          footnote={
            stats.data.students_without_access > 0
              ? "Missing a department, seniority, or matching access rule"
              : "Everyone can reach at least one course"
          }
        />
        <StatCard
          label="Average completion"
          value={`${stats.data.average_completion_percentage}%`}
          footnote="Across every student's accessible courses"
        />
        <StatCard
          label="Completed this week"
          value={stats.data.completions_last_7_days}
          footnote="Subchapters finished in the last 7 days"
        />
      </div>

      <div className="section-heading">
        <h2 className="section-title">Catalogue</h2>
        {drafts.length > 0 && (
          <span className="section-note">
            {drafts.length} {drafts.length === 1 ? "course is" : "courses are"} awaiting publish
          </span>
        )}
      </div>

      <div className="table-card">
        <table className="table">
          <thead>
            <tr>
              <th>Course</th>
              <th>Status</th>
              <th>Chapters</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {list.map((course) => (
              <tr key={course.id}>
                <td className="table-title-cell">{course.title}</td>
                <td>
                  <StatusBadge status={course.status} />
                </td>
                <td>{course.num_chapters}</td>
                <td className="table-action-cell">
                  <button
                    className="btn-icon"
                    onClick={() => navigate(`/admin/courses/${course.id}/roster`)}
                  >
                    View roster
                  </button>
                </td>
              </tr>
            ))}
            {list.length === 0 && (
              <tr>
                <td colSpan={4} className="table-empty">
                  No courses yet. Create the first one from the Courses page.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
