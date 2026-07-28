import { useState } from "react";
import { organisationApi } from "../api/endpoints";
import { useAsync } from "../api/useAsync";
import {
  Button,
  ErrorPanel,
  Loading,
  PageTitle,
  StatusBadge,
} from "../components/ui";

export default function AdminDomainSettings() {
  const { data: organisation, loading, error, reload, setData } = useAsync(
    () => organisationApi.getDomain(),
    []
  );

  const [domainInput, setDomainInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [actionError, setActionError] = useState(null);

  if (loading) return <Loading label="Loading domain settings" />;
  if (error) return <ErrorPanel error={error} onRetry={reload} />;

  const recordName = organisation?.custom_domain
    ? `_arnav-verify.${organisation.custom_domain}`
    : null;

  const submitDomain = async (event) => {
    event.preventDefault();
    if (!domainInput.trim()) return;

    setActionError(null);
    setSaving(true);
    try {
      const updated = await organisationApi.setDomain(domainInput.trim());
      setData(updated);
      setDomainInput("");
    } catch (err) {
      setActionError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const verify = async () => {
    setActionError(null);
    setVerifying(true);
    try {
      const updated = await organisationApi.verifyDomain();
      setData(updated);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setVerifying(false);
    }
  };

  const removeDomain = async () => {
    setActionError(null);
    try {
      const updated = await organisationApi.removeDomain();
      setData(updated);
    } catch (err) {
      setActionError(err.message);
    }
  };

  return (
    <div>
      <PageTitle
        eyebrow="Settings"
        title="Custom Domain"
        lede="Serve this learning system from your own domain, such as learn.yourcompany.com."
      />

      {organisation?.custom_domain ? (
        <div className="stat-card" style={{ marginBottom: 24 }}>
          <div className="stat-label">Current domain</div>
          <div className="stat-value" style={{ fontSize: 20 }}>
            {organisation.custom_domain}{" "}
            <StatusBadge
              status={organisation.domain_verified ? "published" : "draft"}
            />
          </div>

          {!organisation.domain_verified && (
            <div style={{ marginTop: 16 }}>
              <p className="page-lede">
                Add this TXT record at your DNS provider, then verify:
              </p>
              <pre className="stat-footnote" style={{ userSelect: "all" }}>
                {recordName}
                {"  TXT  "}
                {organisation.verification_token}
              </pre>
              <Button onClick={verify} disabled={verifying}>
                {verifying ? "Verifying" : "Verify domain"}
              </Button>
            </div>
          )}

          {organisation.domain_verified && (
            <p className="page-lede" style={{ marginTop: 8 }}>
              Point a CNAME (or ALIAS/A record, for an apex domain) at the
              platform's default address, and this domain will serve the app.
            </p>
          )}

          <Button
            variant="ghost"
            onClick={removeDomain}
            style={{ marginTop: 16 }}
          >
            Remove custom domain
          </Button>
        </div>
      ) : (
        <p className="page-lede">No custom domain has been set yet.</p>
      )}

      <form onSubmit={submitDomain} style={{ maxWidth: 420 }}>
        <label className="field-label" htmlFor="custom-domain">
          {organisation?.custom_domain ? "Replace with a new domain" : "Domain"}
        </label>
        <input
          id="custom-domain"
          className="text-input"
          value={domainInput}
          onChange={(e) => setDomainInput(e.target.value)}
          placeholder="learn.yourcompany.com"
        />

        {actionError && <div className="form-error">{actionError}</div>}

        <Button type="submit" disabled={saving} style={{ marginTop: 12 }}>
          {saving ? "Saving" : "Save domain"}
        </Button>
      </form>
    </div>
  );
}
