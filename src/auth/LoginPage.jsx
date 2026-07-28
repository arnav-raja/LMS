import { useState } from "react";
import { useAuth } from "./AuthContext";
import crest from "../assets/crest.png";
import wordmark from "../assets/wordmark.png";

// Sign-in only. There is no "create an account" path here — an
// administrator adds each student from the Students page instead.
export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError(null);
    setBusy(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-screen">
      <img className="login-watermark" src={crest} alt="" aria-hidden="true" />

      <form className="login-card" onSubmit={submit}>
        <img className="login-wordmark" src={wordmark} alt="Arnav — Jewellery from the Heart" />
        <div className="login-subtitle">Learning System</div>

        <label className="field-label" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          className="text-input"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="username"
          placeholder="you@arnav.com"
          required
        />

        <label className="field-label" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className="text-input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        {error && <div className="form-error">{error}</div>}

        <button className="btn btn-gold btn-block" type="submit" disabled={busy}>
          {busy ? "Working" : "Sign in"}
        </button>

        <p className="login-help">
          Don&apos;t have an account? Ask an administrator to add you from the Students page.
        </p>
      </form>
    </div>
  );
}
