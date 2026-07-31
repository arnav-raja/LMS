import { api, request } from "./client";

/*
 * One function per backend route. No route uses a trailing slash — keep it
 * that way, since a mismatch causes a 307 redirect that drops the auth header.
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

  me: () => api.get("/auth/me"),
};

/* ------------------------------------------------------------- courses --- */

export const courseApi = {
  // Admins receive every course; students receive only what their
  // department and seniority grants them.
  list: () => api.get("/courses"),

  publish: (courseId) => api.post(`/courses/${courseId}/publish`),

  archive: (courseId) => api.post(`/courses/${courseId}/archive`),

  chapters: (courseId) => api.get(`/courses/${courseId}/chapters`),

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

/* ----------------------------------------------------- student summary --- */

export const meApi = {
  dashboard: () => api.get("/me/dashboard"),
};

/* ----------------------------------------------------------------- quiz --- */

export const quizApi = {
  // Admin: builder saves the whole quiz (questions + options) in one go.
  save: (chapterId, quiz) => api.post(`/admin/chapters/${chapterId}/quiz`, quiz),

  adminList: () => api.get("/admin/quizzes"),

  adminGet: (quizId) => api.get(`/admin/quizzes/${quizId}`),

  remove: (quizId) => api.delete(`/admin/quizzes/${quizId}`),

  results: (quizId) => api.get(`/admin/quizzes/${quizId}/results`),

  // Student: list across every accessible course, take, and submit.
  mine: () => api.get("/quizzes/me"),

  take: (quizId) => api.get(`/quizzes/${quizId}`),

  submit: (quizId, answers) => api.post(`/quizzes/${quizId}/submit`, { answers }),
};

/* --------------------------------------------------------- certificate --- */

export const certificateApi = {
  mine: () => api.get("/certificates/me"),

  all: (courseId) =>
    api.get(courseId ? `/admin/certificates?course_id=${courseId}` : "/admin/certificates"),
};

// Department and seniority lists are fetched live — see api/referenceData.js
// — instead of being duplicated here as hardcoded constants.
