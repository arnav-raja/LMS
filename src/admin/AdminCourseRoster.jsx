import { useNavigate, useParams } from "react-router-dom";
import { adminApi, departmentLabel } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import { EmptyState, ErrorPanel, Loading, PageTitle, ProgressBar } from "../components/ui";

const formatDate = (value) => {
  if (!value) return "No activity yet";
  return new Date(value).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

export default function AdminCourseRoster() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(
    () => adminApi.courseRoster(courseId),
    [courseId]
  );

  if (loading) return <Loading label="Loading roster" />;

  if (error) {
    return (
      <>
        <button className="back-link" onClick={() => navigate("/admin/courses")}>
          Back to courses
        </button>
        <PageTitle eyebrow="Roster" title="Could not load roster" />
        <ErrorPanel error={error} onRetry={reload} />
      </>
    );
  }

  return (
    <>
      <button className="back-link" onClick={() => navigate("/admin/courses")}>
        Back to courses
      </button>

      <PageTitle
        eyebrow="Roster"
        title={data.course_title}
        lede="Everyone whose department and seniority reaches this course, and how far each has moved."
      />

      {data.students.length === 0 ? (
        <EmptyState
          title="Nobody can reach this course yet"
          body="Grant access to a department and seniority combination, and the people it covers will appear here."
        />
      ) : (
        <div className="table-card">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Department</th>
                <th>Seniority</th>
                <th>Completed</th>
                <th>Progress</th>
                <th>Last activity</th>
              </tr>
            </thead>
            <tbody>
              {data.students.map((student) => (
                <tr key={student.id}>
                  <td className="table-title-cell">{student.name}</td>
                  <td>{departmentLabel(student.department)}</td>
                  <td>{student.seniority || <span className="muted">Not set</span>}</td>
                  <td>
                    {student.completed_subchapters} of {student.total_subchapters}
                  </td>
                  <td>
                    <div className="table-progress">
                      <ProgressBar value={student.percentage} />
                      <span className="table-progress-num">{Math.round(student.percentage)}%</span>
                    </div>
                  </td>
                  <td className="muted">{formatDate(student.last_activity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
