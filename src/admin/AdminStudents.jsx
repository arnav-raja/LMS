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

const blankForm = () => ({
  name: "",
  username: "",
  email: "",
  password: "",
  role: "student",
  department: "",
  seniority: "",
});

/**
 * Full profile editor — this is the old Users feature's functionality,
 * folded in here so every account (student or admin) is managed from one
 * place. Username is the required, primary identifier; email is optional.
 */
function StudentForm({ student, onClose, onSaved }) {
  const editing = Boolean(student);

  const [form, setForm] = useState(
    student
      ? {
          name: student.name,
          username: student.username || "",
          email: student.email || "",
          password: "",
          role: student.role,
          department: student.department || "",
          seniority: student.seniority || "",
        }
      : blankForm()
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const save = async () => {
    setSaving(true);
    setError(null);

    const payload = {
      name: form.name.trim(),
      username: form.username.trim(),
      email: form.email.trim() || null,
      role: form.role,
      department: form.department || null,
      seniority: form.seniority || null,
    };

    // Only send a password if one was typed — leaving it blank while
    // editing means "keep the current password".
    if (form.password.trim()) payload.password = form.password.trim();

    try {
      if (editing) await adminApi.updateUser(student.id, payload);
      else await adminApi.createUser({ ...payload, password: form.password.trim() });
      onSaved();
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  const canSave = form.name.trim() && form.username.trim() && (editing || form.password.trim());

  return (
    <Modal
      eyebrow={editing ? "Edit student" : "New student"}
      title={editing ? student.name : "Add a student"}
      onClose={onClose}
      actions={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={save} disabled={saving || !canSave}>
            {saving ? "Saving" : "Save"}
          </Button>
        </>
      }
    >
      <label className="field-label" htmlFor="student-name">
        Full name
      </label>
      <input id="student-name" className="text-input" value={form.name} onChange={set("name")} />

      <label className="field-label" htmlFor="student-username">
        Username
      </label>
      <input
        id="student-username"
        className="text-input"
        value={form.username}
        onChange={set("username")}
        placeholder="jane.doe"
      />

      <label className="field-label" htmlFor="student-email">
        Email (optional)
      </label>
      <input
        id="student-email"
        className="text-input"
        type="email"
        value={form.email}
        onChange={set("email")}
      />

      <label className="field-label" htmlFor="student-password">
        {editing ? "New password (leave blank to keep current)" : "Password"}
      </label>
      <input
        id="student-password"
        className="text-input"
        type="password"
        value={form.password}
        onChange={set("password")}
      />

      <label className="field-label" htmlFor="student-role">
        Role
      </label>
      <select id="student-role" className="text-input" value={form.role} onChange={set("role")}>
        <option value="student">Student</option>
        <option value="admin">Admin</option>
      </select>

      <label className="field-label" htmlFor="student-dept">
        Department
      </label>
      <select
        id="student-dept"
        className="text-input"
        value={form.department}
        onChange={set("department")}
      >
        <option value="">Not set</option>
        {DEPARTMENTS.map((d) => (
          <option key={d.code} value={d.code}>
            {d.label}
          </option>
        ))}
      </select>

      <label className="field-label" htmlFor="student-sen">
        Seniority
      </label>
      <select
        id="student-sen"
        className="text-input"
        value={form.seniority}
        onChange={set("seniority")}
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

/**
 * Detail panel for one account. Options appear in a fixed order: Roster
 * (the courses reaching them and their progress in each), then Edit (the
 * full profile — this is where the old separate Users feature now lives),
 * then Delete.
 */
function StudentDetail({ record, onClose, onChanged }) {
  const { data, loading, error, reload } = useAsync(
    () => adminApi.studentProgress(record.id),
    [record.id]
  );

  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const remove = async () => {
    if (!window.confirm(`Delete ${record.name}? This cannot be undone.`)) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await adminApi.deleteUser(record.id);
      onChanged();
      onClose();
    } catch (err) {
      setDeleteError(err.message);
      setDeleting(false);
    }
  };

  const courses = data?.courses || [];
  const completedCourses = courses.filter((c) => c.percentage >= 100).length;
  const averagePercentage = courses.length
    ? Math.round(courses.reduce((sum, c) => sum + c.percentage, 0) / courses.length)
    : 0;

  return (
    <>
      <Drawer
        eyebrow="Student"
        title={record.name}
        meta={`${departmentLabel(record.department)} · ${record.seniority || "No seniority set"}${
          record.email ? ` · ${record.email}` : ""
        }`}
        onClose={onClose}
      >
        {/* ------------------------------------------------------- Roster --- */}
        {loading && <Loading label="Loading progress" />}
        {error && <ErrorPanel error={error} onRetry={reload} />}

        {!loading && !error && (
          <>
            <div className="detail-metrics">
              <MetricCard label="Courses reached" value={courses.length} />
              <MetricCard label="Courses completed" value={completedCourses} />
              <MetricCard label="Average completion" value={`${averagePercentage}%`} />
            </div>

            {courses.length === 0 ? (
              <p className="drawer-empty">
                No courses reach this student yet. Grant access to their department and seniority
                from the Courses page.
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
                          const state = sub.is_completed
                            ? "done"
                            : sub.is_locked
                            ? "locked"
                            : "current";
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
          </>
        )}

        {/* --------------------------------------------------- Edit / Delete --- */}
        <div className="detail-actions">
          <Button variant="ghost" onClick={() => setEditing(true)}>
            Edit
          </Button>
          {deleteError && <div className="form-error">{deleteError}</div>}
          <Button variant="ghost" onClick={remove} disabled={deleting}>
            {deleting ? "Deleting" : "Delete"}
          </Button>
        </div>
      </Drawer>

      {editing && (
        <StudentForm
          student={record}
          onClose={() => setEditing(false)}
          onSaved={() => {
            setEditing(false);
            onClose();
            onChanged();
          }}
        />
      )}
    </>
  );
}

export default function AdminStudents() {
  const { data, loading, error, reload } = useAsync(() => adminApi.users(), []);
  const [filter, setFilter] = useState("ALL");
  const [selected, setSelected] = useState(null); // the account row whose detail is open
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
        lede="Every account on Arnav LMS. Add one here, then open a row to see its roster, edit its profile, or remove it."
        action={<Button onClick={() => setCreating(true)}>New student</Button>}
      />

      {students.length === 0 ? (
        <EmptyState
          title="No students yet"
          body="Add your first account below — there is no self sign-up, so every account starts here."
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
                  <th>Username</th>
                  <th>Role</th>
                  <th>Department</th>
                  <th>Seniority</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((student) => (
                  <tr
                    key={student.id}
                    className="table-row-clickable"
                    onClick={() => setSelected(student)}
                  >
                    <td className="table-title-cell">{student.name}</td>
                    <td>{student.username || <span className="muted">Not set</span>}</td>
                    <td>{student.role}</td>
                    <td>{departmentLabel(student.department)}</td>
                    <td>{student.seniority || <span className="muted">Not set</span>}</td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} className="table-empty">
                      No accounts in this department.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {selected && (
        <StudentDetail
          record={selected}
          onClose={() => setSelected(null)}
          onChanged={reload}
        />
      )}

      {creating && (
        <StudentForm
          student={null}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
        />
      )}
    </>
  );
}
