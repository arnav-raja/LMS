import { useState } from "react";
import { certificateApi, courseApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import { EmptyState, ErrorPanel, Loading, PageTitle } from "../components/ui";

const formatDate = (value) => {
  if (!value) return "";
  return new Date(value).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

function CertificateDownloadCell({ certificateId }) {
  const [pending, setPending] = useState(null);

  const download = async (format) => {
    setPending(format);
    try {
      await certificateApi.download(certificateId, format);
    } catch {
      // The row stays put; the student can be told to try again if it
      // keeps failing — no need to disrupt the whole registry over it.
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="chip-row">
      <button
        className="btn btn-ghost btn-small"
        disabled={pending !== null}
        onClick={() => download("pdf")}
      >
        {pending === "pdf" ? "…" : "PDF"}
      </button>
      <button
        className="btn btn-ghost btn-small"
        disabled={pending !== null}
        onClick={() => download("png")}
      >
        {pending === "png" ? "…" : "Image"}
      </button>
    </div>
  );
}

export default function AdminCertificates() {
  const [courseFilter, setCourseFilter] = useState("");
  const [search, setSearch] = useState("");

  const { data: courses } = useAsync(() => courseApi.list(), []);
  const {
    data: certificates,
    loading,
    error,
    reload,
  } = useAsync(() => certificateApi.all(courseFilter || undefined), [courseFilter]);

  if (loading && !certificates) return <Loading label="Loading certificates" />;
  if (error) return <ErrorPanel error={error} onRetry={reload} />;

  const filtered = (certificates || []).filter((certificate) => {
    if (!search.trim()) return true;
    const needle = search.trim().toLowerCase();
    return (
      certificate.user_name.toLowerCase().includes(needle) ||
      (certificate.user_email || "").toLowerCase().includes(needle) ||
      certificate.certificate_number.toLowerCase().includes(needle)
    );
  });

  return (
    <>
      <PageTitle
        eyebrow="Certificates"
        title="Certificate registry"
        lede="Every certificate issued platform-wide, generated automatically the moment a student passes every chapter and quiz in a course."
      />

      <div className="chip-row">
        <select
          className="text-input"
          value={courseFilter}
          onChange={(e) => setCourseFilter(e.target.value)}
        >
          <option value="">All courses</option>
          {(courses || []).map((course) => (
            <option key={course.id} value={course.id}>
              {course.title}
            </option>
          ))}
        </select>

        <input
          className="text-input"
          placeholder="Search by student or certificate number"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="No certificates yet"
          body="Certificates appear here automatically once a student completes every chapter and passes every quiz in a course."
        />
      ) : (
        <div className="table-card">
          <table className="table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Email</th>
                <th>Course</th>
                <th>Certificate number</th>
                <th>Issued</th>
                <th>Download</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((certificate) => (
                <tr key={certificate.id}>
                  <td className="table-title-cell">{certificate.user_name}</td>
                  <td className="muted">{certificate.user_email || "—"}</td>
                  <td>{certificate.course_title}</td>
                  <td>
                    <code>{certificate.certificate_number}</code>
                  </td>
                  <td className="muted">{formatDate(certificate.issued_at)}</td>
                  <td>
                    <CertificateDownloadCell certificateId={certificate.id} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
