import { useState } from "react";
import { courseApi } from "../../api/endpoints";
import { useAsync } from "../../api/useAsync";
import {
  Button,
  EmptyState,
  ErrorPanel,
  Loading,
  PageTitle,
  StatusBadge,
} from "../../components/ui";
import CourseBuilder from "./CourseBuilder";
import CourseDetail from "./CourseDetail";

export default function AdminCourses() {
  const { data, loading, error, reload } = useAsync(() => courseApi.list(), []);
  const [builder, setBuilder] = useState(null); // {} for new course
  const [selected, setSelected] = useState(null); // the course whose detail is open

  const courses = data || [];

  if (loading) return <Loading label="Loading courses" />;

  return (
    <>
      <PageTitle
        eyebrow="Catalogue"
        title="Courses"
        lede="Every course on offer. Open one to see access, roster, edit, delete and archive."
        action={<Button onClick={() => setBuilder({})}>New course</Button>}
      />

      {error && <ErrorPanel error={error} onRetry={reload} />}

      {!error && courses.length === 0 ? (
        <EmptyState
          title="The catalogue is empty"
          body="Create your first course, add its chapters, then grant access to the departments that need it."
          action={<Button onClick={() => setBuilder({})}>New course</Button>}
        />
      ) : (
        <div className="course-grid">
          {courses.map((course) => (
            <article
              className="course-card course-card-clickable"
              key={course.id}
              onClick={() => setSelected(course)}
              role="button"
              tabIndex={0}
            >
              <div className="course-card-top">
                <StatusBadge status={course.status} />
                <span className="course-card-chapters">
                  {course.num_chapters} {course.num_chapters === 1 ? "chapter" : "chapters"}
                </span>
              </div>

              <h3 className="course-card-title">{course.title}</h3>
              <p className="course-card-desc">{course.description}</p>
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

      {selected && (
        <CourseDetail
          course={selected}
          onClose={() => setSelected(null)}
          onChanged={reload}
        />
      )}
    </>
  );
}
