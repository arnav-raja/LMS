import crest from "../assets/crest.png";

export function Eyebrow({ children }) {
  return <div className="eyebrow">{children}</div>;
}

export function PageTitle({ eyebrow, title, lede, action }) {
  return (
    <div className="page-header-row">
      <div>
        {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
        <h1 className="page-title">{title}</h1>
        {lede && <p className="page-lede">{lede}</p>}
      </div>
      {action}
    </div>
  );
}

export function ProgressBar({ value, wide = false }) {
  const safe = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className={`progress-track ${wide ? "progress-track-wide" : ""}`}>
      <div className="progress-fill" style={{ width: `${safe}%` }} />
    </div>
  );
}

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export function StatCard({ label, value, footnote }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {footnote && <div className="stat-footnote">{footnote}</div>}
    </div>
  );
}

export function Button({ variant = "gold", children, ...props }) {
  return (
    <button className={`btn btn-${variant}`} {...props}>
      {children}
    </button>
  );
}

/** Full-page loading state, used while a route's first fetch resolves. */
export function Loading({ label = "Loading" }) {
  return (
    <div className="loading-state">
      <img className="loading-crest" src={crest} alt="" aria-hidden="true" />
      <div className="loading-label">{label}</div>
    </div>
  );
}

/** Inline error panel. Errors state what happened and what to do next. */
export function ErrorPanel({ error, onRetry }) {
  if (!error) return null;
  return (
    <div className="error-panel" role="alert">
      <div className="error-panel-text">{error.message}</div>
      {onRetry && (
        <button className="btn btn-ghost" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

/** An empty screen is an invitation to act, not an apology. */
export function EmptyState({ title, body, action }) {
  return (
    <div className="empty-state">
      <img className="empty-crest" src={crest} alt="" aria-hidden="true" />
      <div className="empty-title">{title}</div>
      {body && <p className="empty-body">{body}</p>}
      {action}
    </div>
  );
}

export function Modal({ title, eyebrow, children, onClose, actions, wide = false }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className={`modal ${wide ? "modal-wide" : ""}`} onClick={(e) => e.stopPropagation()}>
        {eyebrow && <div className="drawer-eyebrow">{eyebrow}</div>}
        {title && <h2 className="drawer-title">{title}</h2>}
        {children}
        {actions && <div className="modal-actions">{actions}</div>}
      </div>
    </div>
  );
}

export function Drawer({ title, eyebrow, meta, children, onClose }) {
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <button className="drawer-close" onClick={onClose}>
          Close
        </button>
        {eyebrow && <div className="drawer-eyebrow">{eyebrow}</div>}
        {title && <h2 className="drawer-title">{title}</h2>}
        {meta && <div className="drawer-meta">{meta}</div>}
        {children}
      </div>
    </div>
  );
}

export function Field({ label, id, children }) {
  return (
    <>
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      {children}
    </>
  );
}
