import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, clearToken, getToken, request, setToken } from "./client";

function mockFetch(status, body, { asText = false } = {}) {
  const payload = asText ? body : JSON.stringify(body);
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    text: async () => (body === undefined ? "" : payload),
  });
}

afterEach(() => {
  clearToken();
});

describe("token storage", () => {
  it("round-trips a token", () => {
    setToken("abc");
    expect(getToken()).toBe("abc");
  });

  it("clears a token", () => {
    setToken("abc");
    clearToken();
    expect(getToken()).toBeNull();
  });

  it("survives storage being unavailable", () => {
    const spy = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("denied");
    });

    // A private window with site data blocked must not crash the app; the
    // session simply does not persist.
    expect(getToken()).toBeNull();
    spy.mockRestore();
  });
});

describe("request", () => {
  it("attaches the bearer token", async () => {
    setToken("my-token");
    const fetchMock = mockFetch(200, { ok: true });

    await request("/thing");

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.Authorization).toBe("Bearer my-token");
  });

  it("omits the header when asked not to authenticate", async () => {
    setToken("my-token");
    const fetchMock = mockFetch(200, { ok: true });

    await request("/auth/login", { auth: false });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.Authorization).toBeUndefined();
  });

  it("sends form bodies url-encoded, as OAuth2 requires", async () => {
    const fetchMock = mockFetch(200, {});

    await request("/auth/login", {
      method: "POST",
      form: { username: "ada", password: "secret" },
      auth: false,
    });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers["Content-Type"]).toBe(
      "application/x-www-form-urlencoded"
    );
    expect(options.body).toBe("username=ada&password=secret");
  });

  it("sends json bodies as json", async () => {
    const fetchMock = mockFetch(200, {});

    await api.post("/thing", { a: 1 });

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers["Content-Type"]).toBe("application/json");
    expect(options.body).toBe('{"a":1}');
  });

  it("returns null for an empty body", async () => {
    mockFetch(204, undefined);
    await expect(request("/thing")).resolves.toBeNull();
  });
});

describe("errors", () => {
  it("reads FastAPI's string detail", async () => {
    mockFetch(404, { detail: "Quiz not found" });

    await expect(request("/thing")).rejects.toMatchObject({
      status: 404,
      message: "Quiz not found",
    });
  });

  it("flattens FastAPI's 422 validation array", async () => {
    mockFetch(422, {
      detail: [
        { loc: ["body", "password"], msg: "field required" },
        { loc: ["body", "name"], msg: "field required" },
      ],
    });

    await expect(request("/thing")).rejects.toThrow(
      "password: field required, name: field required"
    );
  });

  it("survives a non-JSON error body", async () => {
    mockFetch(500, "<html>Internal Server Error</html>", { asText: true });

    await expect(request("/thing")).rejects.toBeInstanceOf(ApiError);
  });

  it("reports an unreachable server as status 0", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("failed"));

    await expect(request("/thing")).rejects.toMatchObject({ status: 0 });
    await expect(request("/thing")).rejects.toThrow(/Cannot reach the server/);
  });

  it("exposes the status categories callers branch on", () => {
    expect(new ApiError(401).isUnauthorised).toBe(true);
    expect(new ApiError(403).isForbidden).toBe(true);
    expect(new ApiError(404).isNotFound).toBe(true);
    expect(new ApiError(429).isRateLimited).toBe(true);
    expect(new ApiError(404).isForbidden).toBe(false);
  });
});
