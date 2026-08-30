import { useState } from "react";
import { accessApi } from "../../api/endpoints";
import { loadReferenceData } from "../../api/referenceData";
import { useAsync } from "../../api/useAsync";
import { Button, ErrorPanel, Loading, Modal } from "../../components/ui";

// "Manager" is the one seniority that means people-management, not tenure —
// every other seniority (Senior/Mid/Junior) is grouped as "Employees" for
// the bulk-access buttons below.
const isManagerSeniority = (seniority) => seniority === "Manager";

export default function AccessEditor({ course, onClose }) {
  const { data, loading, error, reload } = useAsync(() => accessApi.list(course.id), [course.id]);
  const { data: reference } = useAsync(loadReferenceData, []);
  const [pending, setPending] = useState(null);
  const [bulkPending, setBulkPending] = useState(null);
  const [saveError, setSaveError] = useState(null);

  const departments = reference?.departments || [];
  const seniorities = reference?.seniorities || [];
  const rules = data || [];
  const granted = (dept, sen) =>
    rules.some((r) => r.department === dept && r.seniority === sen);

  // A bulk toggle touches every cell, so it excludes individual edits and
  // vice versa; individual cells otherwise stay independently clickable,
  // same as before the bulk buttons existed.
  const anyBulkPending = bulkPending !== null;
  const anyPending = pending !== null || anyBulkPending;

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

  const managerPairs = departments.map((d) => [d.code, "Manager"]);
  const employeePairs = departments.flatMap((d) =>
    seniorities.filter((s) => !isManagerSeniority(s)).map((s) => [d.code, s])
  );
  const allGranted = (pairs) => pairs.length > 0 && pairs.every(([d, s]) => granted(d, s));

  const toggleGroup = async (key, pairs) => {
    setBulkPending(key);
    setSaveError(null);
    const shouldGrant = !allGranted(pairs);
    try {
      await Promise.all(
        pairs.map(([dept, sen]) =>
          shouldGrant ? accessApi.grant(course.id, dept, sen) : accessApi.revoke(course.id, dept, sen)
        )
      );
      reload();
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setBulkPending(null);
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
        <>
          <div className="chip-row">
            <button
              type="button"
              className={`chip ${allGranted(managerPairs) ? "chip-active" : ""}`}
              onClick={() => toggleGroup("managers", managerPairs)}
              disabled={anyPending}
              aria-pressed={allGranted(managerPairs)}
            >
              {bulkPending === "managers" ? "Updating…" : "Managers"}
            </button>
            <button
              type="button"
              className={`chip ${allGranted(employeePairs) ? "chip-active" : ""}`}
              onClick={() => toggleGroup("employees", employeePairs)}
              disabled={anyPending}
              aria-pressed={allGranted(employeePairs)}
            >
              {bulkPending === "employees" ? "Updating…" : "Employees"}
            </button>
          </div>

          <div className="access-grid">
            <div className="access-grid-corner" />
            {seniorities.map((s) => (
              <div key={s} className="access-col-label">
                {s}
              </div>
            ))}

            {departments.map((d) => (
              <div className="access-row" key={d.code}>
                <div className="access-row-label">{d.label}</div>
                {seniorities.map((s) => {
                  const on = granted(d.code, s);
                  const cellKey = `${d.code}-${s}`;
                  const cellBusy = pending === cellKey;
                  return (
                    <button
                      key={s}
                      className={`access-cell ${on ? "access-cell-on" : ""} ${cellBusy ? "access-cell-busy" : ""}`}
                      onClick={() => toggle(d.code, s)}
                      disabled={cellBusy || anyBulkPending}
                      aria-pressed={on}
                      aria-label={`${on ? "Revoke" : "Grant"} ${d.label} ${s}`}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </>
      )}
    </Modal>
  );
}
