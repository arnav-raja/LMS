import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  BookOpen,
  GraduationCap,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { departmentLabel } from "../api/endpoints";
import crest from "../assets/crest.png";
import wordmark from "../assets/wordmark.png";

const ADMIN_LINKS = [
  { to: "/admin", label: "Dashboard", end: true, icon: LayoutDashboard },
  { to: "/admin/students", label: "Students", icon: Users },
  { to: "/admin/courses", label: "Courses", icon: BookOpen },
];

const STUDENT_LINKS = [
  { to: "/", label: "My learning", end: true, icon: GraduationCap },
  { to: "/courses", label: "Courses", icon: BookOpen },
];

const COLLAPSE_KEY = "arnav.sidebarCollapsed";

export default function Shell() {
  const { user, isAdmin, logout } = useAuth();
  const links = isAdmin ? ADMIN_LINKS : STUDENT_LINKS;

  const [collapsed, setCollapsed] = useState(() => {
    try {
      return window.localStorage.getItem(COLLAPSE_KEY) === "true";
    } catch {
      return false;
    }
  });

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(COLLAPSE_KEY, String(next));
      } catch {
        /* preference just won't persist */
      }
      return next;
    });
  };

  return (
    <div className={`app-shell ${collapsed ? "app-shell-collapsed" : ""}`}>
      <aside className="sidebar">
        <button
          className="sidebar-collapse-toggle"
          onClick={toggleCollapsed}
          aria-label={collapsed ? "Expand menu" : "Collapse menu"}
          title={collapsed ? "Expand menu" : "Collapse menu"}
        >
          {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>

        <div className="sidebar-brand">
          <img className="sidebar-crest" src={crest} alt="" aria-hidden="true" />
          <img className="sidebar-wordmark" src={wordmark} alt="Arnav" />
          <div className="sidebar-tagline">
            {isAdmin ? "Admin" : "Learning"}
          </div>
        </div>

        <nav className="sidebar-nav">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? "sidebar-link-active" : ""}`
                }
                title={collapsed ? link.label : undefined}
              >
                <Icon size={17} className="sidebar-link-icon" />
                <span className="sidebar-link-label">{link.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">{user?.name}</div>
          <div className="sidebar-user-meta">
            {isAdmin
              ? "Administrator"
              : [departmentLabel(user?.department), user?.seniority]
                  .filter(Boolean)
                  .join(" · ") || "Awaiting access profile"}
          </div>
          <button
            className="sidebar-signout"
            onClick={logout}
            title={collapsed ? "Sign out" : undefined}
          >
            <LogOut size={15} />
            <span className="sidebar-signout-label">Sign out</span>
          </button>
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}