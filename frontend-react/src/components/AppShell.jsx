export default function AppShell({ user, children }) {
  return (
    <div className="app-shell">
      <header className="shell-header">
        <div>
          <p className="eyebrow">FlowLogix</p>
          <h1>Operations Console</h1>
        </div>
        <nav aria-label="Primary" className="shell-nav">
          <a className="active" href="#">Orders</a>
          <a href="#" aria-disabled="true">Warehouse</a>
          <a href="#" aria-disabled="true">Delivered</a>
          <a href="#" aria-disabled="true">Users</a>
        </nav>
        <div className="user-chip" aria-label="Signed in user">
          <span>{user?.username || "unknown"}</span>
          <strong>{user?.role || "user"}</strong>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
