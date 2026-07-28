import { useState } from "react";
import { useAuth } from "./AuthContext";
import { authApi } from "../api/endpoints";
import crest from "../assets/crest.png";
import wordmark from "../assets/wordmark.png";

export default function LoginPage() {
  const { login } = useAuth();
  const [mode, setMode] = useState("signin");
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);

    try {
      if (mode === "signin") {
        await login(identifier, password);
      } else {
        await authApi.register(name, username, email, password);
        setNotice("Account created. Sign in to continue.");
        setMode("signin");
        setPassword("");
      }
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

        {mode === "register" && (
          <>
            <label className="field-label" htmlFor="name">
              Full name
            </label>
            <input
              id="name"
              className="text-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              required
            />

            <label className="field-label" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              className="text-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              placeholder="jane.doe"
              required
            />

            <label className="field-label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              className="text-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              placeholder="you@arnav.com"
              required
            />
          </>
        )}

        {mode === "signin" && (
          <>
            <label className="field-label" htmlFor="identifier">
              Username or Email
            </label>
            <input
              id="identifier"
              className="text-input"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              autoComplete="username"
              placeholder="jane.doe or you@arnav.com"
              required
            />
          </>
        )}

        <label className="field-label" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className="text-input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={mode === "signin" ? "current-password" : "new-password"}
          required
        />

        {error && <div className="form-error">{error}</div>}
        {notice && <div className="form-notice">{notice}</div>}

        <button className="btn btn-gold btn-block" type="submit" disabled={busy}>
          {busy ? "Working" : mode === "signin" ? "Sign in" : "Create account"}
        </button>

        <button
          type="button"
          className="login-switch"
          onClick={() => {
            setMode(mode === "signin" ? "register" : "signin");
            setError(null);
            setNotice(null);
          }}
        >
          {mode === "signin" ? "Create an account" : "I already have an account"}
        </button>
      </form>
    </div>
  );
}
