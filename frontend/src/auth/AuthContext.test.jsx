import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "./AuthContext";
import { authApi } from "../api/endpoints";
import { getToken, setToken } from "../api/client";

vi.mock("../api/endpoints", () => ({
  authApi: { login: vi.fn(), me: vi.fn() },
}));

const ADA = {
  id: 1,
  name: "Ada Lovelace",
  username: "ada",
  email: "ada@example.com",
  role: "student",
  department: "EC",
  seniority: "Mid",
};

function Probe() {
  const { user, loading, isAdmin, isAuthenticated, login, logout } = useAuth();

  if (loading) return <div>loading</div>;

  return (
    <div>
      <div data-testid="who">{user ? user.name : "nobody"}</div>
      <div data-testid="admin">{String(isAdmin)}</div>
      <div data-testid="authed">{String(isAuthenticated)}</div>
      <button onClick={() => login("ada", "correct-horse-battery")}>sign in</button>
      <button onClick={logout}>sign out</button>
    </div>
  );
}

function renderAuth() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
}

beforeEach(() => {
  authApi.login.mockReset();
  authApi.me.mockReset();
});

describe("restoring a session", () => {
  it("stays signed out when there is no token", async () => {
    renderAuth();

    expect(await screen.findByTestId("authed")).toHaveTextContent("false");
    expect(authApi.me).not.toHaveBeenCalled();
  });

  it("signs the user back in when the stored token still works", async () => {
    setToken("stored-token");
    authApi.me.mockResolvedValue(ADA);

    renderAuth();

    expect(await screen.findByTestId("who")).toHaveTextContent("Ada Lovelace");
  });

  it("discards a token the API no longer accepts", async () => {
    setToken("stale-token");
    authApi.me.mockRejectedValue(
      Object.assign(new Error("Could not validate credentials"), {
        status: 401,
        isUnauthorised: true,
      })
    );

    renderAuth();

    await waitFor(() => expect(getToken()).toBeNull());
  });
});

describe("signing in and out", () => {
  it("stores the token and the user", async () => {
    const user = userEvent.setup();
    authApi.login.mockResolvedValue({ access_token: "fresh", token_type: "bearer" });
    authApi.me.mockResolvedValue(ADA);

    renderAuth();
    await user.click(await screen.findByRole("button", { name: "sign in" }));

    expect(await screen.findByTestId("who")).toHaveTextContent("Ada Lovelace");
    expect(getToken()).toBe("fresh");
  });

  it("recognises an admin", async () => {
    const user = userEvent.setup();
    authApi.login.mockResolvedValue({ access_token: "fresh" });
    authApi.me.mockResolvedValue({ ...ADA, role: "admin" });

    renderAuth();
    await user.click(await screen.findByRole("button", { name: "sign in" }));

    expect(await screen.findByTestId("admin")).toHaveTextContent("true");
  });

  it("signing out clears the token", async () => {
    const user = userEvent.setup();
    authApi.login.mockResolvedValue({ access_token: "fresh" });
    authApi.me.mockResolvedValue(ADA);

    renderAuth();
    await user.click(await screen.findByRole("button", { name: "sign in" }));
    await screen.findByTestId("who");

    await user.click(screen.getByRole("button", { name: "sign out" }));

    expect(await screen.findByTestId("authed")).toHaveTextContent("false");
    expect(getToken()).toBeNull();
  });
});

describe("a token rejected mid-session", () => {
  it("signs the user out rather than leaving them on a dead page", async () => {
    // Reachable without the token expiring: it stops working the moment an
    // admin resets that account's password or changes its role.
    const user = userEvent.setup();
    authApi.login.mockResolvedValue({ access_token: "fresh" });
    authApi.me.mockResolvedValue(ADA);

    renderAuth();
    await user.click(await screen.findByRole("button", { name: "sign in" }));
    await screen.findByTestId("who");

    // Stand in for any authenticated request coming back 401.
    const { request } = await import("../api/client");
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ detail: "Could not validate credentials" }),
    });

    await request("/anything").catch(() => {});

    await waitFor(() =>
      expect(screen.getByTestId("authed")).toHaveTextContent("false")
    );
    expect(getToken()).toBeNull();
  });

  it("a failed sign-in does not trigger the sign-out path", async () => {
    // The login route answers 401 for a wrong password, but nobody is
    // signed in to be signed out of.
    setToken("still-valid");

    const { request } = await import("../api/client");
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ detail: "Invalid email or password" }),
    });

    await request("/auth/login", { auth: false }).catch(() => {});

    expect(getToken()).toBe("still-valid");
  });
});
