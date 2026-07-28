import { useState } from "react";
import { DEPARTMENTS, SENIORITIES, adminApi, departmentLabel } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import {
  Button,
  Drawer,
  EmptyState,
  ErrorPanel,
  Loading,
  MetricCard,
  Modal,
  PageTitle,
  ProgressBar,
} from "../components/ui";

/**
 * Detail panel for a single student. Options appear in a fixed order:
 * Roster (the courses reaching this student, and their progress in each),
 * then Edit (department / seniority), then Delete.
 */
function StudentDetail({ studentId, onClose, onChanged }) {
  const { data, loading, error, reload } = useAsync(
    () => adminApi.studentProgress(studentId),
    [studentId]
  );

  const [department, setDepartment] = useState("");
  const [seniority, setSeniority] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const openEditor = () => {
    setDepartment(data?.department || "");
    setSeniority(data?.seniority || "");
    setSaveError(null);
    setEditing(true);
  };

  const saveProfile = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      await adminApi.setAccessProfile(studentId, department, seniority);
      setEditing(false);
      reload();
      onChanged?.();
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete ${data.name}? This cannot be undone.`)) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await adminApi.deleteStudent(studentId);
      onChanged?.();
      onClose();
    } catch (err) {
      setDeleteError(err.message);
      setDeleting(false);
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

  const courses = data.courses || [];
  const completedCourses = courses.filter((c) => c.percentage >= 100).length;
  const averagePercentage = courses.length
    ? Math.round(courses.reduce((sum, c) => sum + c.percentage, 0) / courses.length)
    : 0;

  return (
    <Drawer
      eyebrow="Student"
      title={data.name}
      meta={`${departmentLabel(data.department)} · ${data.seniority || "No seniority set"} · ${data.email}`}
      onClose={onClose}
    >
      <div className="detail-metrics">
        <MetricCard label="Courses reached" value={courses.length} />
        <MetricCard label="Courses completed" value={completedCourses} />
        <MetricCard label="Average completion" value={`${averagePercentage}%`} />
      </div>

      {/* --------------------------------------------------------- Roster --- */}
      {courses.length === 0 ? (
        <p className="drawer-empty">
          No courses reach this student yet. Grant access to their department and seniority from
          the Courses page.
        </p>
      ) : (
        courses.map((course) => (
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
        ))
      )}

      {/* ----------------------------------------------------------- Edit --- */}
      <div className="detail-actions">
        {!editing ? (
          <Button variant="ghost" onClick={openEditor}>
            Edit
          </Button>
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
                onClick={saveProfile}
                disabled={saving || !department || !seniority}
              >
                {saving ? "Saving" : "Save profile"}
              </button>
            </div>
          </div>
        )}

        {/* --------------------------------------------------------- Delete --- */}
        {deleteError && <div className="form-error">{deleteError}</div>}
        <Button variant="ghost" onClick={remove} disabled={deleting}>
          {deleting ? "Deleting" : "Delete"}
        </Button>
      </div>
    </Drawer>
  );
}

/** Admins add students directly here — there is no public sign-up page. */
function StudentCreate({ onClose, onCreated }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [department, setDepartment] = useState("");
  const [seniority, setSeniority] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await adminApi.createStudent({
        name: name.trim(),
        email: email.trim(),
        password,
        department: department || null,
        seniority: seniority || null,
      });
      onCreated();
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  return (
    <Modal
      eyebrow="New student"
      title="Add a student"
      onClose={onClose}
      actions={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={save} disabled={saving || !name.trim() || !email.trim() || !password}>
            {saving ? "Adding" : "Add student"}
          </Button>
        </>
      }
    >
      <label className="field-label" htmlFor="new-name">
        Full name
      </label>
      <input
        id="new-name"
        className="text-input"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <label className="field-label" htmlFor="new-email">
        Email
      </label>
      <input
        id="new-email"
        className="text-input"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <label className="field-label" htmlFor="new-password">
        Temporary password
      </label>
      <input
        id="new-password"
        className="text-input"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <label className="field-label" htmlFor="new-dept">
        Department (optional)
      </label>
      <select
        id="new-dept"
        className="text-input"
        value={department}
        onChange={(e) => setDepartment(e.target.value)}
      >
        <option value="">Not set</option>
        {DEPARTMENTS.map((d) => (
          <option key={d.code} value={d.code}>
            {d.label}
          </option>
        ))}
      </select>

      <label className="field-label" htmlFor="new-sen">
        Seniority (optional)
      </label>
      <select
        id="new-sen"
        className="text-input"
        value={seniority}
        onChange={(e) => setSeniority(e.target.value)}
      >
        <option value="">Not set</option>
        {SENIORITIES.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      {error && <ErrorPanel error={error} />}
    </Modal>
  );
}

export default function AdminStudents() {
  const { data, loading, error, reload } = useAsync(() => adminApi.students(), []);
  const [filter, setFilter] = useState("ALL");
  const [selectedId, setSelectedId] = useState(null);
  const [creating, setCreating] = useState(false);

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
        lede="Everyone with an account. Add students here, then open one to see their roster, edit their profile, or remove them."
        action={<Button onClick={() => setCreating(true)}>New student</Button>}
      />

      {students.length === 0 ? (
        <EmptyState
          title="No students yet"
          body="Add your first student — there is no self sign-up, so every account starts here."
          action={<Button onClick={() => setCreating(true)}>New student</Button>}
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
          onChanged={reload}
        />
      )}

      {creating && (
        <StudentCreate
          onClose={() => setCreating(false)}
          onCreated={() => {
            setCreating(false);
            reload();
          }}
        />
      )}
    </>
  );
}
