import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  DEPARTMENTS,
  SENIORITIES,
  accessApi,
  courseApi,
  courseBuilderApi,
} from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import {
  Button,
  EmptyState,
  ErrorPanel,
  Loading,
  Modal,
  PageTitle,
  StatusBadge,
} from "../components/ui";

const blankSubchapter = () => ({ title: "", content: "" });
const blankChapter = () => ({ title: "", description: "", subchapters: [blankSubchapter()] });

function CourseBuilder({ course, onClose, onSaved }) {
  const editing = Boolean(course);

  const [title, setTitle] = useState(course?.title || "");
  const [description, setDescription] = useState(course?.description || "");
  const [status, setStatus] = useState(course?.status || "draft");
  const [chapters, setChapters] = useState([blankChapter()]);
  const [loadingChapters, setLoadingChapters] = useState(editing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // The course list endpoint only returns a count of chapters, so when
  // editing we pull the full structure before populating the form.
  useEffect(() => {
    if (!editing) return;
    let cancelled = false;

    courseApi
      .chapters(course.id)
      .then((data) => {
        if (cancelled) return;
        const mapped = data.map((chapter) => ({
          title: chapter.title,
          description: chapter.description || "",
          subchapters: chapter.subchapters.length
            ? chapter.subchapters.map((sub) => ({
                title: sub.title,
                content: sub.content || "",
              }))
            : [blankSubchapter()],
        }));
        setChapters(mapped.length ? mapped : [blankChapter()]);
      })
      .catch((err) => !cancelled && setError(err))
      .finally(() => !cancelled && setLoadingChapters(false));

    return () => {
      cancelled = true;
    };
  }, [editing, course]);

  const updateChapter = (index, patch) =>
    setChapters(chapters.map((c, i) => (i === index ? { ...c, ...patch } : c)));

  const updateSubchapter = (chapterIndex, subIndex, patch) =>
    setChapters(
      chapters.map((c, i) =>
        i === chapterIndex
          ? {
              ...c,
              subchapters: c.subchapters.map((s, j) => (j === subIndex ? { ...s, ...patch } : s)),
            }
          : c
      )
    );

  const save = async () => {
    setSaving(true);
    setError(null);

    const payload = {
      title: title.trim(),
      description: description.trim(),
      status,
      chapters: chapters
        .filter((c) => c.title.trim())
        .map((c) => ({
          title: c.title.trim(),
          description: c.description.trim() || null,
          subchapters: c.subchapters
            .filter((s) => s.title.trim())
            .map((s) => ({ title: s.title.trim(), content: s.content.trim() || null })),
        })),
    };

    try {
      if (editing) await courseBuilderApi.update(course.id, payload);
      else await courseBuilderApi.create(payload);
      onSaved();
    } catch (err) {
      setError(err);
      setSaving(false);
    }
  };

  return (
    <Modal
      wide
      eyebrow={editing ? "Edit course" : "New course"}
      title={editing ? course.title : "Create a course"}
      onClose={onClose}
      actions={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={save} disabled={saving || !title.trim() || loadingChapters}>
            {saving ? "Saving" : "Save course"}
          </Button>
        </>
      }
    >
      {loadingChapters ? (
        <Loading label="Loading course structure" />
      ) : (
        <>
          <label className="field-label" htmlFor="course-title">
            Title
          </label>
          <input
            id="course-title"
            className="text-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Diamond grading fundamentals"
          />

          <label className="field-label" htmlFor="course-desc">
            Description
          </label>
          <textarea
            id="course-desc"
            className="text-input textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What this course covers, in a sentence or two."
          />

          <label className="field-label" htmlFor="course-status">
            Status
          </label>
          <select
            id="course-status"
            className="text-input"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>

          <div className="builder-heading">Chapters</div>

          {chapters.map((chapter, chapterIndex) => (
            <div className="builder-chapter" key={chapterIndex}>
              <div className="builder-chapter-head">
                <span className="builder-chapter-number">Chapter {chapterIndex + 1}</span>
                {chapters.length > 1 && (
                  <button
                    className="btn-icon btn-icon-quiet"
                    onClick={() => setChapters(chapters.filter((_, i) => i !== chapterIndex))}
                  >
                    Remove chapter
                  </button>
                )}
              </div>

              <input
                className="text-input"
                value={chapter.title}
                onChange={(e) => updateChapter(chapterIndex, { title: e.target.value })}
                placeholder="Chapter title"
              />
              <input
                className="text-input builder-spaced"
                value={chapter.description}
                onChange={(e) => updateChapter(chapterIndex, { description: e.target.value })}
                placeholder="Chapter description (optional)"
              />

              {chapter.subchapters.map((sub, subIndex) => (
                <div className="builder-sub" key={subIndex}>
                  <input
                    className="text-input"
                    value={sub.title}
                    onChange={(e) =>
                      updateSubchapter(chapterIndex, subIndex, { title: e.target.value })
                    }
                    placeholder={`Subchapter ${subIndex + 1} title`}
                  />
                  <textarea
                    className="text-input textarea builder-spaced"
                    value={sub.content}
                    onChange={(e) =>
                      updateSubchapter(chapterIndex, subIndex, { content: e.target.value })
                    }
                    placeholder="Lesson content"
                  />
                  {chapter.subchapters.length > 1 && (
                    <button
                      className="btn-icon btn-icon-quiet"
                      onClick={() =>
                        updateChapter(chapterIndex, {
                          subchapters: chapter.subchapters.filter((_, j) => j !== subIndex),
                        })
                      }
                    >
                      Remove subchapter
                    </button>
                  )}
                </div>
              ))}

              <button
                className="btn btn-ghost btn-small"
                onClick={() =>
                  updateChapter(chapterIndex, {
                    subchapters: [...chapter.subchapters, blankSubchapter()],
                  })
                }
              >
                Add subchapter
              </button>
            </div>
          ))}

          <button
            className="btn btn-ghost btn-small"
            onClick={() => setChapters([...chapters, blankChapter()])}
          >
            Add chapter
          </button>

          {error && <ErrorPanel error={error} />}
        </>
      )}
    </Modal>
  );
}

function AccessEditor({ course, onClose }) {
  const { data, loading, error, reload } = useAsync(() => accessApi.list(course.id), [course.id]);
  const [pending, setPending] = useState(null);
  const [saveError, setSaveError] = useState(null);

  const rules = data || [];
  const granted = (dept, sen) =>
    rules.some((r) => r.department === dept && r.seniority === sen);

  const toggle = async (dept, sen) => {
    const key = `${dept}-${sen}`;
    setPending(key);
    setSaveError(null);
    try {
      if (granted(dept, sen)) await accessApi.revoke(course.id, dept, sen);
      else await accessApi.grant(course.id, dept, sen);
      reload();
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setPending(null);
    }
  };

  return (
    <Modal wide eyebrow="Access" title={course.title} onClose={onClose} actions={
      <Button onClick={onClose}>Done</Button>
    }>
      <p className="modal-lede">
        Tick the department and seniority combinations that may open this course once it is
        published.
      </p>

      {loading && <Loading label="Loading access rules" />}
      {error && <ErrorPanel error={error} onRetry={reload} />}
      {saveError && <div className="form-error">{saveError}</div>}

      {!loading && !error && (
        <div className="access-grid">
          <div className="access-grid-corner" />
          {SENIORITIES.map((s) => (
            <div key={s} className="access-col-label">
              {s}
            </div>
          ))}

          {DEPARTMENTS.map((d) => (
            <div className="access-row" key={d.code}>
              <div className="access-row-label">{d.label}</div>
              {SENIORITIES.map((s) => {
                const on = granted(d.code, s);
                const busy = pending === `${d.code}-${s}`;
                return (
                  <button
                    key={s}
                    className={`access-cell ${on ? "access-cell-on" : ""} ${busy ? "access-cell-busy" : ""}`}
                    onClick={() => toggle(d.code, s)}
                    disabled={busy}
                    aria-pressed={on}
                    aria-label={`${on ? "Revoke" : "Grant"} ${d.label} ${s}`}
                  />
                );
              })}
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}

export default function AdminCourses() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(() => courseApi.list(), []);
  const [builder, setBuilder] = useState(null); // { course } or {} for new
  const [accessCourse, setAccessCourse] = useState(null);
  const [actionError, setActionError] = useState(null);

  const courses = data || [];

  const toggleStatus = async (course) => {
    setActionError(null);
    try {
      if (course.status === "published") await courseApi.archive(course.id);
      else await courseApi.publish(course.id);
      reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const remove = async (course) => {
    if (!window.confirm(`Delete "${course.title}"? This cannot be undone.`)) return;
    setActionError(null);
    try {
      await courseBuilderApi.remove(course.id);
      reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  if (loading) return <Loading label="Loading courses" />;

  return (
    <>
      <PageTitle
        eyebrow="Catalogue"
        title="Courses"
        lede="Build, publish, and decide who may open each course."
        action={<Button onClick={() => setBuilder({})}>New course</Button>}
      />

      {error && <ErrorPanel error={error} onRetry={reload} />}
      {actionError && <div className="form-error">{actionError}</div>}

      {!error && courses.length === 0 ? (
        <EmptyState
          title="The catalogue is empty"
          body="Create your first course, add its chapters, then grant access to the departments that need it."
          action={<Button onClick={() => setBuilder({})}>New course</Button>}
        />
      ) : (
        <div className="course-grid">
          {courses.map((course) => (
            <article className="course-card" key={course.id}>
              <div className="course-card-top">
                <StatusBadge status={course.status} />
                <span className="course-card-chapters">
                  {course.num_chapters} {course.num_chapters === 1 ? "chapter" : "chapters"}
                </span>
              </div>

              <h3 className="course-card-title">{course.title}</h3>
              <p className="course-card-desc">{course.description}</p>

              <div className="course-card-actions">
                <button className="btn-icon" onClick={() => setBuilder({ course })}>
                  Edit
                </button>
                <button className="btn-icon" onClick={() => setAccessCourse(course)}>
                  Access
                </button>
                <button
                  className="btn-icon"
                  onClick={() => navigate(`/admin/courses/${course.id}/roster`)}
                >
                  Roster
                </button>
                <button className="btn-icon" onClick={() => toggleStatus(course)}>
                  {course.status === "published" ? "Archive" : "Publish"}
                </button>
                <button className="btn-icon btn-icon-danger" onClick={() => remove(course)}>
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {builder && (
        <CourseBuilder
          course={builder.course}
          onClose={() => setBuilder(null)}
          onSaved={() => {
            setBuilder(null);
            reload();
          }}
        />
      )}

      {accessCourse && (
        <AccessEditor course={accessCourse} onClose={() => setAccessCourse(null)} />
      )}
    </>
  );
}
