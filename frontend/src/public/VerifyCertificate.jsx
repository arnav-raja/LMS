import { useState } from "react";
import { useParams } from "react-router-dom";
import { Award, CheckCircle2, XCircle } from "lucide-react";
import { certificateApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import { useMutation } from "../api/useMutation";
import crest from "../assets/crest.png";
import wordmark from "../assets/wordmark.png";

const formatDate = (value) => {
  if (!value) return "";
  return new Date(value).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
};

function Result({ certificate }) {
  return (
    <div className="verify-result verify-result-valid">
      <CheckCircle2 size={22} />
      <div>
        <div className="verify-headline">This certificate is genuine.</div>
        <p className="verify-detail">
          <strong>{certificate.holder_name}</strong> completed{" "}
          <strong>{certificate.course_title}</strong> on{" "}
          {formatDate(certificate.issued_at)}.
        </p>
        <div className="muted">
          Certificate number <code>{certificate.certificate_number}</code>
        </div>
      </div>
    </div>
  );
}

function NotFound({ message }) {
  return (
    <div className="verify-result verify-result-invalid">
      <XCircle size={22} />
      <div>
        <div className="verify-headline">No certificate matches that number.</div>
        <p className="verify-detail">{message}</p>
        <p className="muted">
          Check the number against the certificate — it is easy to confuse
          0 with O. Certificates are also removed when the person's account
          is deleted.
        </p>
      </div>
    </div>
  );
}

/**
 * The one page in the application that needs no account.
 *
 * Somebody handed a certificate — a recruiter, an auditor, a client — has
 * no login here, and until now had no way at all to tell whether the
 * number printed on it meant anything.
 *
 * Reachable either with the number in the URL (from a link or QR code) or
 * by typing it in.
 */
export default function VerifyCertificate() {
  const { certificateNumber } = useParams();
  const [typed, setTyped] = useState("");

  // When the number is in the URL, check it immediately.
  const fromUrl = useAsync(
    () =>
      certificateNumber
        ? certificateApi.verify(certificateNumber)
        : Promise.resolve(null),
    [certificateNumber]
  );

  const [manualResult, setManualResult] = useState(null);
  const check = useMutation(() => certificateApi.verify(typed), {
    onSuccess: setManualResult,
  });

  const certificate = manualResult || fromUrl.data;
  const error = check.error || (certificateNumber ? fromUrl.error : null);
  const busy = check.busy || (certificateNumber && fromUrl.loading);

  return (
    <div className="login-screen">
      <img className="login-watermark" src={crest} alt="" aria-hidden="true" />

      <div className="login-card verify-card">
        <img className="login-wordmark" src={wordmark} alt="Arnav" />
        <div className="login-subtitle">
          <Award size={15} /> Certificate check
        </div>

        <p className="login-help verify-lede">
          Enter the number printed on a certificate to confirm it was issued
          by Arnav and who it belongs to.
        </p>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            setManualResult(null);
            check.run();
          }}
        >
          <label className="field-label" htmlFor="certificate-number">
            Certificate number
          </label>
          <input
            id="certificate-number"
            className="text-input"
            value={typed || certificateNumber || ""}
            onChange={(event) => {
              setTyped(event.target.value);
              setManualResult(null);
            }}
            placeholder="ARNAV-XXXXXXXXXXXXXXXX"
            autoComplete="off"
          />

          <button
            className="btn btn-gold btn-block"
            type="submit"
            disabled={busy || !(typed || certificateNumber || "").trim()}
          >
            {busy ? "Checking" : "Check certificate"}
          </button>
        </form>

        {certificate && !error && <Result certificate={certificate} />}
        {error && <NotFound message={error.message} />}
      </div>
    </div>
  );
}
