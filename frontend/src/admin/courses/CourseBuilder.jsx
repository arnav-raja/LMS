import { useEffect, useState } from "react";
import { courseApi, courseBuilderApi } from "../../api/endpoints";
import { useMutation } from "../../api/useMutation";
import { Button, ErrorPanel, Loading, Modal } from "../../components/ui";

// `id` is what tells the API this is an existing chapter or lesson rather
// than a new one, so a save keeps the same rows and every student's
// progress recorded against them stays attached. New items carry null,
// and the API creates them. Without this the API would match by position,
// and reordering two chapters would swap their students' history.
const blankSubchapter = () => ({ id: null, title: "", content: "" });
const blankChapter = () => ({
  id: null,
  title: "",
  description: "",
  subchapters: [blankSubchapter()],
});

export default function CourseBuilder({ course, onClose, onSaved }) {
  const editing = Boolean(course);

  const [title, setTitle] = useState(course?.title || "");
  const [description, setDescription] = useState(course?.description || "");
  const [status, setStatus] = useState(course?.status || "draft");
  const [chapters, setChapters] = useState([blankChapter()]);
  const [loadingChapters, setLoadingChapters] = useState(editing);
  // Only for the initial structure fetch. The save has its own error,
  // carried by the mutation below.
  const [loadError, setLoadError] = useState(null);

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
          id: chapter.id,
          title: chapter.title,
          description: chapter.description || "",
          subchapters: chapter.subchapters.length
            ? chapter.subchapters.map((sub) => ({
                id: sub.id,
                title: sub.title,
                content: sub.content || "",
              }))
            : [blankSubchapter()],
        }));
        setChapters(mapped.length ? mapped : [blankChapter()]);
      })
      .catch((err) => !cancelled && setLoadError(err))
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

  const buildPayload = () => ({
    title: title.trim(),
    description: description.trim(),
    status,
    chapters: chapters
      .filter((c) => c.title.trim())
      .map((c) => ({
        // `id` is what tells the API this is the same chapter, moved,
        // rather than a new one — see the note by blankChapter above.
        id: c.id ?? null,
        title: c.title.trim(),
        description: c.description.trim() || null,
        subchapters: c.subchapters
          .filter((s) => s.title.trim())
          .map((s) => ({
            id: s.id ?? null,
            title: s.title.trim(),
            content: s.content.trim() || null,
          })),
      })),
  });

  const save = useMutation(
    () =>
      editing
        ? courseBuilderApi.update(course.id, buildPayload())
        : courseBuilderApi.create(buildPayload()),
    { onSuccess: onSaved }
  );

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
          <Button onClick={save.run} disabled={save.busy || !title.trim() || loadingChapters}>
            {save.busy ? "Saving" : "Save course"}
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

          {(loadError || save.error) && <ErrorPanel error={loadError || save.error} />}
        </>
      )}
    </Modal>
  );
}
