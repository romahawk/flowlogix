import {
  Activity,
  BookOpen,
  LayoutDashboard,
  LogOut,
  Moon,
  Plus,
  Sun,
  Truck,
  Warehouse,
} from "lucide-react";

export default function AppShell({ user, darkMode, onToggleDark, backendBase, children }) {
  const toBackend = (path) => `${backendBase}${path}`;

  return (
    <div className={`app-root ${darkMode ? "theme-dark" : "theme-light"}`}>
      <header className="topbar">
        <div className="brand-area">
          <div className="brand-logo" aria-hidden="true">FL</div>
          <h1>FlowLogix</h1>
          <a className="onboarding-chip" href="#" aria-disabled="true">
            <BookOpen size={14} />
            Onboarding
          </a>
        </div>

        <nav className="main-nav" aria-label="Primary">
          <a className="nav-btn active" href="/dashboard">
            <LayoutDashboard size={16} />
            Dashboard
          </a>
          <a className="nav-btn" href={toBackend("/warehouse")}>
            <Warehouse size={16} />
            Warehouse
          </a>
          <a className="nav-btn" href={toBackend("/delivered")}>
            <Truck size={16} />
            Delivered
          </a>
          <a className="nav-btn add" href="#" aria-disabled="true">
            <Plus size={16} />
            Add New Order
          </a>
          <a className="nav-btn" href={toBackend("/activity_logs")}>
            <Activity size={16} />
            Activity Logs
          </a>
        </nav>

        <div className="user-actions">
          <span className="user-badge">{user?.username || "demo"} ({user?.role || "user"})</span>
          <a className="logout-link" href={toBackend("/logout")} aria-label="Log out">
            <LogOut size={16} />
          </a>
          <button
            type="button"
            className={`theme-toggle ${darkMode ? "on" : "off"}`}
            onClick={onToggleDark}
            aria-label="Toggle dark mode"
          >
            <span className="theme-thumb" />
            <span className="theme-icon">{darkMode ? <Sun size={12} /> : <Moon size={12} />}</span>
          </button>
        </div>
      </header>
      <main className="app-shell">{children}</main>
    </div>
  );
}