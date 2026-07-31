import { useState } from "react";
import { Award } from "lucide-react";
import { certificateApi } from "../api/endpoints";
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

function CertificateDownloads({ certificateId }) {
  const [pending, setPending] = useState(null);
  const [error, setError] = useState(null);

  const download = async (format) => {
    setPending(format);
    setError(null);
    try {
      await certificateApi.download(certificateId, format);
    } catch (err) {
      setError(err.detail || "Couldn't download the certificate.");
    } finally {
      setPending(null);
    }
  };

  return (
    <div>
      <div className="chip-row" style={{ marginTop: 12 }}>
        <button
          className="btn btn-ghost btn-small"
          disabled={pending !== null}
          onClick={() => download("pdf")}
        >
          {pending === "pdf" ? "Preparing…" : "Download PDF"}
        </button>
        <button
          className="btn btn-ghost btn-small"
          disabled={pending !== null}
          onClick={() => download("png")}
        >
          {pending === "png" ? "Preparing…" : "Download PNG"}
        </button>
      </div>
      {error && (
        <div className="muted" style={{ marginTop: 6, color: "var(--danger, #b34141)" }}>
          {error}
        </div>
      )}
    </div>
  );
}

export default function StudentCertificates() {
  const { data: certificates, loading, error, reload } = useAsync(
    () => certificateApi.mine(),
    []
  );

  if (loading) return <Loading label="Loading your certificates" />;
  if (error) return <ErrorPanel error={error} onRetry={reload} />;

  return (
    <>
      <PageTitle
        eyebrow="Certificates"
        title="Your certificates"
        lede="Earned automatically the moment you complete every chapter and pass every quiz in a course."
      />

      {certificates.length === 0 ? (
        <EmptyState
          title="No certificates yet"
          body="Complete every chapter and quiz in a course to earn its certificate — it will appear here the moment you do."
        />
      ) : (
        <div className="course-grid">
          {certificates.map((certificate) => (
            <div className="course-card" key={certificate.id}>
              <div className="course-card-top">
                <Award size={20} />
                <div className="course-card-title">{certificate.course_title}</div>
              </div>
              <div className="course-card-desc">
                Certificate number <code>{certificate.certificate_number}</code>
              </div>
              <div className="course-card-next muted">
                Issued {formatDate(certificate.issued_at)}
              </div>
              <CertificateDownloads certificateId={certificate.id} />
            </div>
          ))}
        </div>
      )}
    </>
  );
}
