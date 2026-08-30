const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

const TOKEN_KEY = "arnav.token";

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }

  get isUnauthorised() {
    return this.status === 401;
  }

  get isForbidden() {
    return this.status === 403;
  }

  get isNotFound() {
    return this.status === 404;
  }

  // Sign-in is rate limited per identifier. The detail explains the wait,
  // so callers generally just show the message.
  get isRateLimited() {
    return this.status === 429;
  }
}

/*
 * Called whenever the API rejects a request as unauthenticated. The auth
 * layer registers a handler here at start-up so an expired or revoked
 * token drops the user back to the sign-in screen.
 *
 * This matters more than it used to: a token is now invalidated the moment
 * an admin resets that account's password or changes its role, so a
 * signed-in user can be rejected mid-session rather than only when their
 * token expires. Without this they would sit on a page whose every request
 * fails, with no indication why.
 */
let unauthorisedHandler = null;

export function onUnauthorised(handler) {
  unauthorisedHandler = handler;
}

export function getToken() {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable — session will simply not persist */
  }
}

export function clearToken() {
  setToken(null);
}

/**
 * FastAPI returns errors as { detail: ... }. `detail` is a string for
 * HTTPException, but an array of objects for 422 validation failures.
 */
function readDetail(payload, status) {
  if (!payload) return null;
  const detail = payload.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : null;
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .join(", ");
  }
  return `Request failed with status ${status}`;
}

async function parseResponse(response) {
  if (response.status === 204) return null;
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/**
 * Core request helper. Attaches the bearer token, unwraps JSON, and raises
 * ApiError on any non-2xx response so callers can branch on status.
 */
export async function request(path, { method = "GET", body, form, headers = {}, auth = true } = {}) {
  const finalHeaders = { ...headers };
  let payload;

  if (form) {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    payload = new URLSearchParams(form).toString();
    finalHeaders["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    finalHeaders["Content-Type"] = "application/json";
  }

  if (auth) {
    const token = getToken();
    if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: payload,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check that the API is running.");
  }

  const data = await parseResponse(response);

  if (!response.ok) {
    const error = new ApiError(response.status, readDetail(data, response.status));

    // A failed sign-in is a 401 too, but the user is not signed in to be
    // signed out of — only authenticated requests should trigger this.
    if (error.isUnauthorised && auth && unauthorisedHandler) {
      unauthorisedHandler(error);
    }

    throw error;
  }

  return data;
}

export const api = {
  get: (path, options) => request(path, { ...options, method: "GET" }),
  post: (path, body, options) => request(path, { ...options, method: "POST", body }),
  put: (path, body, options) => request(path, { ...options, method: "PUT", body }),
  patch: (path, body, options) => request(path, { ...options, method: "PATCH", body }),
  delete: (path, body, options) => request(path, { ...options, method: "DELETE", body }),
};
