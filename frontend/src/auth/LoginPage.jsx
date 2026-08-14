import { useState } from "react";
import { useAuth } from "./AuthContext";
import crest from "../assets/crest.png";
import wordmark from "../assets/wordmark.png";

// Sign-in only — there is no "create an account" path here. Every account
// is added by an administrator from the Students page instead (see
// src/admin/AdminStudents.jsx), and can be reached at sign-in by either
// its username or its email, if one was ever set.
export default function LoginPage() {
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError(null);
    setBusy(true);

    try {
      await login(identifier, password);
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
        <div className="login-subtitle">Arnav LMS</div>

        <label className="field-label" htmlFor="identifier">
          Username
        </label>
        <input
          id="identifier"
          className="text-input"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          autoComplete="username"
          placeholder="jane.doe"
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
