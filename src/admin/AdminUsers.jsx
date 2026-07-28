import { useState } from "react";
import { DEPARTMENTS, SENIORITIES, adminApi, departmentLabel } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import {
  Button,
  EmptyState,
  ErrorPanel,
  Loading,
  Modal,
  PageTitle,
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

function UserForm({ user, onClose, onSaved }) {
  const editing = Boolean(user);

  const [form, setForm] = useState(
    user
      ? {
          name: user.name,
          username: user.username || "",
          email: user.email,
          password: "",
          role: user.role,
          department: user.department || "",
          seniority: user.seniority || "",
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
      email: form.email.trim(),
      role: form.role,
      department: form.department || null,
      seniority: form.seniority || null,
    };

    // Only send a password if one was typed — leaving it blank while
    // editing means "keep the current password".
    if (form.password.trim()) payload.password = form.password.trim();

    try {
      if (editing) await adminApi.updateUser(user.id, payload);
      else await adminApi.createUser({ ...payload, password: form.password.trim() });
      onSaved();
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  const canSave =
    form.name.trim() &&
    form.username.trim() &&
    form.email.trim() &&
    (editing || form.password.trim());

  return (
    <Modal
      eyebrow={editing ? "Edit user" : "New user"}
      title={editing ? user.name : "Create a user"}
      onClose={onClose}
      actions={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={save} disabled={saving || !canSave}>
            {saving ? "Saving" : "Save user"}
          </Button>
        </>
      }
    >
      <label className="field-label" htmlFor="user-name">
        Name
      </label>
      <input
        id="user-name"
        className="text-input"
        value={form.name}
        onChange={set("name")}
      />

      <label className="field-label" htmlFor="user-username">
        Username
      </label>
      <input
        id="user-username"
        className="text-input"
        value={form.username}
        onChange={set("username")}
      />

      <label className="field-label" htmlFor="user-email">
        Email
      </label>
      <input
        id="user-email"
        className="text-input"
        type="email"
        value={form.email}
        onChange={set("email")}
      />

      <label className="field-label" htmlFor="user-password">
        {editing ? "New password (leave blank to keep current)" : "Password"}
      </label>
      <input
        id="user-password"
        className="text-input"
        type="password"
        value={form.password}
        onChange={set("password")}
      />

      <label className="field-label" htmlFor="user-role">
        Role
      </label>
      <select id="user-role" className="text-input" value={form.role} onChange={set("role")}>
        <option value="student">Student</option>
        <option value="admin">Admin</option>
      </select>

      <label className="field-label" htmlFor="user-dept">
        Department
      </label>
      <select
        id="user-dept"
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

      <label className="field-label" htmlFor="user-seniority">
        Seniority
      </label>
      <select
        id="user-seniority"
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

export default function AdminUsers() {
  const { data, loading, error, reload } = useAsync(() => adminApi.users(), []);
  const [editorUser, setEditorUser] = useState(null); // null = closed, {} = new
  const [actionError, setActionError] = useState(null);

  const users = data || [];

  const remove = async (user) => {
    if (!window.confirm(`Delete "${user.name}"? This cannot be undone.`)) return;
    setActionError(null);
    try {
      await adminApi.deleteUser(user.id);
      reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  if (loading) return <Loading label="Loading users" />;

  return (
    <>
      <PageTitle
        eyebrow="People"
        title="Users"
        lede="Add, edit, and remove any account — students and admins alike."
        action={<Button onClick={() => setEditorUser({})}>New user</Button>}
      />

      {error && <ErrorPanel error={error} onRetry={reload} />}
      {actionError && <div className="form-error">{actionError}</div>}

      {!error && users.length === 0 ? (
        <EmptyState
          title="No users yet"
          body="Create the first account below."
          action={<Button onClick={() => setEditorUser({})}>New user</Button>}
        />
      ) : (
        !error && (
          <div className="table-card">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Department</th>
                  <th>Seniority</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="table-title-cell">{user.name}</td>
                    <td>{user.username || <span className="muted">Not set</span>}</td>
                    <td>{user.email}</td>
                    <td>{user.role}</td>
                    <td>{departmentLabel(user.department)}</td>
                    <td>{user.seniority || <span className="muted">Not set</span>}</td>
                    <td className="table-action-cell">
                      <button className="btn-icon" onClick={() => setEditorUser(user)}>
                        Edit
                      </button>
                      <button
                        className="btn-icon btn-icon-danger"
                        onClick={() => remove(user)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {editorUser && (
        <UserForm
          user={editorUser.id ? editorUser : null}
          onClose={() => setEditorUser(null)}
          onSaved={() => {
            setEditorUser(null);
            reload();
          }}
        />
      )}
    </>
  );
}
