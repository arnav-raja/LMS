import { api, request } from "./client";

/*
 * One function per backend route. Trailing slashes are deliberate and match
 * the FastAPI router definitions exactly — /courses/ has one, /admin/courses
 * does not. Getting these wrong causes a redirect that drops the auth header.
 */

/* ---------------------------------------------------------------- auth --- */

export const authApi = {
  // OAuth2PasswordRequestForm's field is always called `username`, but the
  // backend accepts either an account's username or its email in it.
  login: (identifier, password) =>
    request("/auth/login", {
      method: "POST",
      form: { username: identifier, password },
      auth: false,
    }),

  register: (name, username, email, password) =>
    request("/auth/register", {
      method: "POST",
      body: { name, username, email, password },
      auth: false,
    }),

  me: () => api.get("/auth/me"),
};

/* ------------------------------------------------------------- courses --- */

export const courseApi = {
  // Admins receive every course; students receive only what their
  // department and seniority grants them.
  list: () => api.get("/courses/"),

  publish: (courseId) => api.post(`/courses/${courseId}/publish`),

  archive: (courseId) => api.post(`/courses/${courseId}/archive`),

  chapters: (courseId) => api.get(`/courses/${courseId}/chapters/`),

  chapter: (courseId, chapterId) => api.get(`/courses/${courseId}/chapters/${chapterId}`),
};

/* ------------------------------------------------------ course builder --- */

export const courseBuilderApi = {
  create: (course) => api.post("/admin/courses", course),

  update: (courseId, course) => api.put(`/admin/courses/${courseId}`, course),

  remove: (courseId) => api.delete(`/admin/courses/${courseId}`),
};

/* -------------------------------------------------------------- access --- */

export const accessApi = {
  list: (courseId) => api.get(`/admin/courses/${courseId}/access`),

  grant: (courseId, department, seniority) =>
    api.post(`/admin/courses/${courseId}/access`, { department, seniority }),

  // This DELETE carries a JSON body, matching GrantAccessRequest.
  revoke: (courseId, department, seniority) =>
    api.delete(`/admin/courses/${courseId}/access`, { department, seniority }),
};

/* --------------------------------------------------------------- admin --- */

export const adminApi = {
  dashboard: () => api.get("/admin/dashboard"),

  departments: () => api.get("/admin/departments"),

  roles: () => api.get("/admin/roles"),

  students: () => api.get("/admin/students"),

  studentProgress: (userId) => api.get(`/admin/students/${userId}/progress`),

  courseRoster: (courseId) => api.get(`/admin/courses/${courseId}/students`),

  setAccessProfile: (userId, department, seniority) =>
    api.patch(`/admin/users/${userId}/access-profile`, { department, seniority }),

  users: () => api.get("/admin/users"),

  createUser: (user) => api.post("/admin/users", user),

  updateUser: (userId, changes) => api.patch(`/admin/users/${userId}`, changes),

  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
};

/* ------------------------------------------------------------ learning --- */

export const learningApi = {
  // Returns 404 with "Course completed" once every subchapter is done.
  // Callers should treat that as a state, not a failure.
  continueCourse: (courseId) => api.get(`/learning/courses/${courseId}/continue`),

  progress: (courseId) => api.get(`/learning/courses/${courseId}/progress`),
};

/* ------------------------------------------------------------ progress --- */

export const progressApi = {
  complete: (subchapterId) => api.post("/progress/complete", { subchapter_id: subchapterId }),

  mine: () => api.get("/progress/me"),
};

/* ------------------------------------------------------- organisation --- */

export const organisationApi = {
  getDomain: () => api.get("/admin/organisation/domain"),

  setDomain: (customDomain) =>
    api.post("/admin/organisation/domain", { custom_domain: customDomain }),

  verifyDomain: () => api.post("/admin/organisation/domain/verify"),

  removeDomain: () => api.delete("/admin/organisation/domain"),
};

/* ----------------------------------------------------- student summary --- */

export const meApi = {
  dashboard: () => api.get("/me/dashboard"),
};

/* ----------------------------------------------------------- constants --- */

export const DEPARTMENTS = [
  { code: "CR", label: "Customer Relations" },
  { code: "DE", label: "Design" },
  { code: "EC", label: "E-Commerce" },
  { code: "FI", label: "Finance" },
  { code: "HR", label: "Human Resources" },
  { code: "IN", label: "Inventory" },
  { code: "MK", label: "Marketing" },
  { code: "OP", label: "Operations" },
  { code: "SA", label: "Sales" },
];

export const SENIORITIES = ["Manager", "Senior", "Mid", "Junior"];

export const departmentLabel = (code) =>
  DEPARTMENTS.find((d) => d.code === code)?.label || code || "Unassigned";
