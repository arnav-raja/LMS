import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../api/endpoints";
import { clearToken, getToken, onUnauthorised, setToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Any authenticated request the API rejects signs the user out, which
  // sends them back to the login screen instead of leaving them on a page
  // whose every request quietly fails.
  //
  // This is reachable mid-session, not only on expiry: a token stops
  // working the moment an admin resets that account's password or changes
  // its role.
  useEffect(() => {
    onUnauthorised(() => {
      clearToken();
      setUser(null);
    });

    return () => onUnauthorised(null);
  }, []);

  // On first load, if a token is already in storage, confirm it still works.
  useEffect(() => {
    let cancelled = false;

    async function restore() {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await authApi.me();
        if (!cancelled) setUser(me);
      } catch {
        clearToken();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restore();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (identifier, password) => {
    const { access_token: token } = await authApi.login(identifier, password);
    setToken(token);
    const me = await authApi.me();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      logout,
      isAdmin: user?.role === "admin",
      isAuthenticated: Boolean(user),
    }),
    [user, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside an AuthProvider");
  return context;
}
