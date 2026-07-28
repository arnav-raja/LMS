import { useState } from "react";
import { DEPARTMENTS, SENIORITIES, adminApi, departmentLabel } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import {
  Drawer,
  EmptyState,
  ErrorPanel,
  Loading,
  PageTitle,
  ProgressBar,
} from "../components/ui";

function StudentDetail({ studentId, onClose, onProfileSaved }) {
  const { data, loading, error, reload } = useAsync(
    () => adminApi.studentProgress(studentId),
    [studentId]
  );

  const [department, setDepartment] = useState("");
  const [seniority, setSeniority] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [editing, setEditing] = useState(false);

  const openEditor = () => {
    setDepartment(data?.department || "");
    setSeniority(data?.seniority || "");
    setSaveError(null);
    setEditing(true);
  };

  const save = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      await adminApi.setAccessProfile(studentId, department, seniority);
      setEditing(false);
      reload();
      onProfileSaved?.();
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Drawer eyebrow="Student" title="Loading" onClose={onClose}>
        <Loading label="Loading progress" />
      </Drawer>
    );
  }

  if (error) {
    return (
      <Drawer eyebrow="Student" title="Could not load" onClose={onClose}>
        <ErrorPanel error={error} onRetry={reload} />
      </Drawer>
    );
  }

  return (
    <Drawer
      eyebrow="Student"
      title={data.name}
      meta={`${departmentLabel(data.department)} · ${data.seniority || "No seniority set"} · ${data.email}`}
      onClose={onClose}
    >
      {!editing ? (
        <button className="btn btn-ghost btn-small" onClick={openEditor}>
          Change access profile
        </button>
      ) : (
        <div className="inline-editor">
          <label className="field-label" htmlFor="dept">
            Department
          </label>
          <select
            id="dept"
            className="text-input"
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
          >
            <option value="">Select a department</option>
            {DEPARTMENTS.map((d) => (
              <option key={d.code} value={d.code}>
                {d.label}
              </option>
            ))}
          </select>

          <label className="field-label" htmlFor="sen">
            Seniority
          </label>
          <select
            id="sen"
            className="text-input"
            value={seniority}
            onChange={(e) => setSeniority(e.target.value)}
          >
            <option value="">Select a seniority</option>
            {SENIORITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          {saveError && <div className="form-error">{saveError}</div>}

          <div className="inline-editor-actions">
            <button className="btn btn-ghost btn-small" onClick={() => setEditing(false)}>
              Cancel
            </button>
            <button
              className="btn btn-gold btn-small"
              onClick={save}
              disabled={saving || !department || !seniority}
            >
              {saving ? "Saving" : "Save profile"}
            </button>
          </div>
        </div>
      )}

      {data.courses.length === 0 && (
        <p className="drawer-empty">
          No courses reach this student yet. Grant access to their department and seniority from the
          Courses page.
        </p>
      )}

      {data.courses.map((course) => (
        <div className="drawer-course" key={course.course_id}>
          <div className="drawer-course-header">
            <span className="drawer-course-title">{course.title}</span>
            <span className="drawer-course-pct">{Math.round(course.percentage)}%</span>
          </div>
          <ProgressBar value={course.percentage} wide />

          {course.chapters.map((chapter) => (
            <div className="drawer-chapter" key={chapter.id}>
              <div className="drawer-chapter-title">
                {chapter.chapter_number}. {chapter.title}
              </div>
              <ul className="chapter-list">
                {chapter.subchapters.map((sub) => {
                  const state = sub.is_completed ? "done" : sub.is_locked ? "locked" : "current";
                  return (
                    <li key={sub.id} className={`chapter-item chapter-${state}`}>
                      <span className="chapter-dot" />
                      <span className="chapter-item-title">{sub.title}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      ))}
    </Drawer>
  );
}

export default function AdminStudents() {
  const { data, loading, error, reload } = useAsync(() => adminApi.students(), []);
  const [filter, setFilter] = useState("ALL");
  const [selectedId, setSelectedId] = useState(null);

  if (loading) return <Loading label="Loading students" />;

  if (error) {
    return (
      <>
        <PageTitle eyebrow="People" title="Students" />
        <ErrorPanel error={error} onRetry={reload} />
      </>
    );
  }

  const students = data || [];
  const filtered = filter === "ALL" ? students : students.filter((s) => s.department === filter);

  return (
    <>
      <PageTitle
        eyebrow="People"
        title="Students"
        lede="Everyone with an account, and the department and seniority that decides what they can open."
      />

      {students.length === 0 ? (
        <EmptyState
          title="No students yet"
          body="Once people register through the sign-up screen, they will appear here ready for an access profile."
        />
      ) : (
        <>
          <div className="chip-row">
            <button
              className={`chip ${filter === "ALL" ? "chip-active" : ""}`}
              onClick={() => setFilter("ALL")}
            >
              All
            </button>
            {DEPARTMENTS.map((d) => (
              <button
                key={d.code}
                className={`chip ${filter === d.code ? "chip-active" : ""}`}
                onClick={() => setFilter(d.code)}
              >
                {d.label}
              </button>
            ))}
          </div>

          <div className="table-card">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Department</th>
                  <th>Seniority</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((student) => (
                  <tr
                    key={student.id}
                    className="table-row-clickable"
                    onClick={() => setSelectedId(student.id)}
                  >
                    <td className="table-title-cell">{student.name}</td>
                    <td>{student.email}</td>
                    <td>{departmentLabel(student.department)}</td>
                    <td>{student.seniority || <span className="muted">Not set</span>}</td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={4} className="table-empty">
                      No students in this department.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {selectedId && (
        <StudentDetail
          studentId={selectedId}
          onClose={() => setSelectedId(null)}
          onProfileSaved={reload}
        />
      )}
    </>
  );
}
