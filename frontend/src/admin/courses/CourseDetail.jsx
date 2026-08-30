import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { accessApi, adminApi, courseApi, courseBuilderApi } from "../../api/endpoints";
import { useAsync } from "../../api/useAsync";
import { useMutation } from "../../api/useMutation";
import { Button, Drawer, MetricCard, StatusBadge } from "../../components/ui";
import AccessEditor from "./AccessEditor";
import CourseBuilder from "./CourseBuilder";

/**
 * Detail panel for a single course. Shows computed metrics up top, then
 * the actions in a fixed order: Access, Roster, Edit, Delete, Archive.
 */
export default function CourseDetail({ course, onClose, onChanged }) {
  const navigate = useNavigate();
  const rules = useAsync(() => accessApi.list(course.id), [course.id]);
  const roster = useAsync(() => adminApi.courseRoster(course.id), [course.id]);

  const [showAccess, setShowAccess] = useState(false);
  const [showEdit, setShowEdit] = useState(false);

  const students = roster.data?.students || [];
  const averagePercentage = students.length
    ? Math.round(students.reduce((sum, s) => sum + s.percentage, 0) / students.length)
    : 0;

  const goToRoster = () => {
    onClose();
    navigate(`/admin/courses/${course.id}/roster`);
  };

  const closeAndRefresh = () => {
    onClose();
    onChanged();
  };

  const toggleStatus = useMutation(
    () =>
      course.status === "published"
        ? courseApi.archive(course.id)
        : courseApi.publish(course.id),
    { onSuccess: closeAndRefresh }
  );

  const remove = useMutation(() => courseBuilderApi.remove(course.id), {
    onSuccess: closeAndRefresh,
  });

  const confirmRemove = () => {
    // Deleting a course takes its content and every student's progress
    // against it, so this asks first.
    if (!window.confirm(`Delete "${course.title}"? This cannot be undone.`)) return;
    remove.run();
  };

  const actionError = toggleStatus.error || remove.error;
  const busy = toggleStatus.busy || remove.busy;

  return (
    <>
      <Drawer
        eyebrow="Course"
        title={course.title}
        meta={<StatusBadge status={course.status} />}
        onClose={onClose}
      >
        <p className="drawer-meta">{course.description}</p>

        <div className="detail-metrics">
          <MetricCard label="Chapters" value={course.num_chapters} />
          <MetricCard
            label="Access rules granted"
            value={rules.loading ? "—" : rules.data?.length ?? 0}
          />
          <MetricCard
            label="Students reached"
            value={roster.loading ? "—" : students.length}
          />
          <MetricCard
            label="Average completion"
            value={roster.loading ? "—" : `${averagePercentage}%`}
          />
        </div>

        {actionError && <div className="form-error">{actionError.message}</div>}

        <div className="detail-actions">
          <Button variant="ghost" onClick={() => setShowAccess(true)}>
            Access
          </Button>
          <Button variant="ghost" onClick={goToRoster}>
            Roster
          </Button>
          <Button variant="ghost" onClick={() => setShowEdit(true)}>
            Edit
          </Button>
          <Button variant="ghost" onClick={confirmRemove} disabled={busy}>
            Delete
          </Button>
          <Button variant="ghost" onClick={toggleStatus.run} disabled={busy}>
            {course.status === "published" ? "Archive" : "Publish"}
          </Button>
        </div>
      </Drawer>

      {showAccess && <AccessEditor course={course} onClose={() => setShowAccess(false)} />}

      {showEdit && (
        <CourseBuilder
          course={course}
          onClose={() => setShowEdit(false)}
          onSaved={() => {
            setShowEdit(false);
            onClose();
            onChanged();
          }}
        />
      )}
    </>
  );
}
