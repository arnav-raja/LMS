import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import LoginPage from "./auth/LoginPage";
import Shell from "./components/Shell";
import ErrorBoundary from "./components/ErrorBoundary";
import { Loading } from "./components/ui";

import StudentDashboard from "./student/StudentDashboard";
import StudentCourses from "./student/StudentCourses";
import CoursePlayer from "./student/CoursePlayer";
import StudentQuizzes from "./student/StudentQuizzes";
import QuizTake from "./student/QuizTake";
import StudentCertificates from "./student/StudentCertificates";
import VerifyCertificate from "./public/VerifyCertificate";

// The admin pages are the bulk of the application and most people here
// are students, who can never open any of them. Loading them lazily keeps
// the course builder and quiz builder out of a student's first download.
const AdminDashboard = lazy(() => import("./admin/AdminDashboard"));
const AdminStudents = lazy(() => import("./admin/AdminStudents"));
const AdminCourses = lazy(() => import("./admin/courses/AdminCourses"));
const AdminCourseRoster = lazy(() => import("./admin/AdminCourseRoster"));
const AdminQuizzes = lazy(() => import("./admin/AdminQuizzes"));
const AdminCertificates = lazy(() => import("./admin/AdminCertificates"));

function AdminOnly({ children }) {
  const { isAdmin } = useAuth();
  if (!isAdmin) return <Navigate to="/" replace />;

  return (
    <Suspense fallback={<Loading label="Loading" />}>{children}</Suspense>
  );
}

function Routing() {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) return <Loading label="Signing you in" />;

  // Checking a certificate is deliberately outside the sign-in wall.
  // Whoever is handed one — a recruiter, an auditor — has no account here,
  // so this must resolve before `isAuthenticated` is consulted.
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/verify" element={<VerifyCertificate />} />
        <Route path="/verify/:certificateNumber" element={<VerifyCertificate />} />
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  return (
    <Routes>
      {/* Available signed in too, so an admin can check a number without
          signing out first. */}
      <Route path="/verify" element={<VerifyCertificate />} />
      <Route path="/verify/:certificateNumber" element={<VerifyCertificate />} />
      <Route element={<Shell />}>
        {/* Admins land on their dashboard; students land on their learning. */}
        <Route index element={isAdmin ? <Navigate to="/admin" replace /> : <StudentDashboard />} />

        <Route path="courses" element={<StudentCourses />} />
        <Route path="courses/:courseId" element={<CoursePlayer />} />
        <Route path="quizzes" element={<StudentQuizzes />} />
        <Route path="quizzes/:quizId" element={<QuizTake />} />
        <Route path="certificates" element={<StudentCertificates />} />

        <Route
          path="admin"
          element={
            <AdminOnly>
              <AdminDashboard />
            </AdminOnly>
          }
        />
        <Route
          path="admin/students"
          element={
            <AdminOnly>
              <AdminStudents />
            </AdminOnly>
          }
        />
        <Route
          path="admin/courses"
          element={
            <AdminOnly>
              <AdminCourses />
            </AdminOnly>
          }
        />
        <Route
          path="admin/courses/:courseId/roster"
          element={
            <AdminOnly>
              <AdminCourseRoster />
            </AdminOnly>
          }
        />
        <Route
          path="admin/quizzes"
          element={
            <AdminOnly>
              <AdminQuizzes />
            </AdminOnly>
          }
        />
        <Route
          path="admin/certificates"
          element={
            <AdminOnly>
              <AdminCertificates />
            </AdminOnly>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routing />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
