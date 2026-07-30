import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import LoginPage from "./auth/LoginPage";
import Shell from "./components/Shell";
import { Loading } from "./components/ui";

import AdminDashboard from "./admin/AdminDashboard";
import AdminStudents from "./admin/AdminStudents";
import AdminCourses from "./admin/AdminCourses";
import AdminCourseRoster from "./admin/AdminCourseRoster";
import AdminQuizzes from "./admin/AdminQuizzes";
import AdminCertificates from "./admin/AdminCertificates";

import StudentDashboard from "./student/StudentDashboard";
import StudentCourses from "./student/StudentCourses";
import CoursePlayer from "./student/CoursePlayer";
import StudentQuizzes from "./student/StudentQuizzes";
import QuizTake from "./student/QuizTake";
import StudentCertificates from "./student/StudentCertificates";

function AdminOnly({ children }) {
  const { isAdmin } = useAuth();
  return isAdmin ? children : <Navigate to="/" replace />;
}

function Routing() {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) return <Loading label="Signing you in" />;
  if (!isAuthenticated) return <LoginPage />;

  return (
    <Routes>
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
    <BrowserRouter>
      <AuthProvider>
        <Routing />
      </AuthProvider>
    </BrowserRouter>
  );
}