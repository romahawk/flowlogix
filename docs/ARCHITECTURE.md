# FlowLogix — Architecture Document

**Version:** 1.0
**Date:** 2026-02-24
**Status:** Active

---

## High-Level Overview

FlowLogix is a server-rendered Flask application with an API-first migration strategy.
The current production path is the Flask/Jinja2 legacy UI, progressively hardened by
formalizing a JSON API layer (v1) that will eventually support a React consumer.

```
Browser
  │
  ├── Legacy UI (Flask/Jinja2 + Vanilla JS)
  │     Jinja templates → Flask routes → SQLAlchemy → SQLite
  │
  └── API v1 (JSON, Blueprint /api/v1)
        Flask Blueprint → RBAC decorators → SQLAlchemy → SQLite
```

---

## Key Components

### Backend (`app/`)

| Component | Path | Responsibility |
|-----------|------|----------------|
| App factory | `app/__init__.py` | Flask init, blueprints, demo mode, seeding hooks |
| Models | `app/models.py` | ORM: User, Order, WarehouseStock, DeliveredGoods, AuditLog, ArchivedOrder, StockReportEntry, ActivityLog |
| Routes (legacy) | `app/routes/` | Jinja-rendered pages: dashboard, orders, warehouse, delivered, analytics, admin, auth |
| API v1 | `app/api/v1/` | JSON endpoints: `/api/v1/orders`, `/api/v1/auth/me` |
| Schemas | `app/api/v1/schemas.py` | Request/response validation and serialization |
| Errors | `app/api/v1/errors.py` | Structured JSON error envelopes with `trace_id` |
| Decorators | `app/decorators.py` | RBAC enforcement (`@require_role`) |
| Database | `app/database.py` | SQLAlchemy `db` instance, `init_db()` |
| Seed | `app/seed_boot.py` | Demo-safe, date-aware seeder |

### Frontend (Legacy) (`app/static/`, `app/templates/`)

| Component | Path | Notes |
|-----------|------|-------|
| Dashboard JS | `app/static/js/dashboard.js` | 1007-line monolith — targeted for modularization in Sprint 3 |
| Analytics JS | `app/static/js/analytics.js` | Analytics page interactivity |
| Global CSS | `app/static/css/style.css` | 588 lines — shared styles across all pages |
| Templates | `app/templates/` | Jinja2 HTML; `base.html` provides layout shell |

### Frontend (Experimental React) (`frontend-react/`)

React 18 + Vite SPA, consuming API v1. **Not the production path** (see ADR-0006).
Component inventory: `AppShell`, `OrdersToolbar`, `OrdersTable`, `Pagination`,
`ErrorBanner`, `EmptyState`. Dev proxy forwards `/api/*` to Flask on port 5000.

### Migrations (`migrations/`)

Alembic-managed schema migrations via `flask db upgrade`. SQLite for local/demo;
DATABASE_URL can be swapped for PostgreSQL without code changes.

---

## Data Flow

### Legacy Read Path (Dashboard Orders Table)

```
User loads /dashboard
  → Flask route (dashboard_routes.py)
    → SQLAlchemy query (filter + sort + paginate)
      → Jinja template renders HTML table
        → dashboard.js handles client-side UX (pagination controls, timeline)
```

### API Read Path (v1)

```
GET /api/v1/orders?page=1&per_page=10&sort=eta:desc&filter[transit_status]=In+Transit
  → RBAC check (@login_required + role decorator)
    → Strict query validation (schemas.py → 400 on bad params)
      → SQLAlchemy query (server-side filter/sort/paginate)
        → JSON envelope response {data, pagination, trace_id}
```

### Write Path (Legacy Forms)

```
POST /orders/add  (or edit/delete)
  → RBAC check
    → Demo readonly guard (app/__init__.py before_request hook)
      → SQLAlchemy write + db.session.commit()
        → AuditLog entry
          → Redirect to orders list
```

---

## Data Model Summary

```
User ──< Order          (user_id FK)
User ──< WarehouseStock (user_id FK)
User ──< DeliveredGoods (user_id FK)
User ──< AuditLog       (user_id FK)
User ──< ActivityLog    (user_id FK)
WarehouseStock ──< StockReportEntry (related_order_id FK)
```

**Known data quality debt:**
- `quantity` stored as `String` in Order, WarehouseStock, DeliveredGoods — should be numeric.
- Most date fields stored as `String(10)` rather than `db.Date` — enables silent format drift.
- `ArchivedOrder` does not FK back to `User` by relationship (loose coupling).

---

## Auth / Session Model

- Flask-Login with server-side session cookies (`SESSION_COOKIE_HTTPONLY=True` by default).
- No JWT. No OAuth. Session cookie auth chosen for simplicity at current scale.
- API v1 reuses the same session cookie — no separate token system yet.
- Unauthorized API requests return JSON 401 (not HTML redirect).
- Demo mode: auto-login to `demo/admin` user on first `GET /` or `/login` visit.

---

## Storage Choices

| Concern | Current Choice | Rationale |
|---------|---------------|-----------|
| Primary DB | SQLite | Zero-config for demo/local; swap to Postgres via `DATABASE_URL` |
| File uploads (POD) | Local filesystem (`uploads/`) | Simple; not cloud-backed |
| Sessions | Server-side cookie (Flask default) | Sufficient at current scale |
| Migrations | Alembic via Flask-Migrate | Standard; enables incremental schema evolution |

---

## Key Tradeoffs

| Decision | Tradeoff |
|----------|---------|
| Legacy-first UI (Jinja2 vs React) | Faster delivery; avoids migration churn. React path frozen until Sprint 5. |
| Server-side sort/filter | Deterministic, RBAC-safe, no client-side data leakage. Adds latency per interaction vs. client-sort. |
| SQLite for demo | Zero-config local experience. Not suitable for multi-user production write load. |
| Cookie session auth | Simple, works with existing Flask-Login. No stateless API key path today. |
| Strict 400 validation | Prevents silent coercion bugs. Requires UI to always send well-formed queries. |
| Monolithic dashboard.js | Fast to iterate initially. Now a regression risk — modularization is Sprint 3. |

---

## Future Scaling Notes

1. **Database:** Swap `DATABASE_URL` to PostgreSQL when concurrency or write volume increases.
   No model changes needed; Alembic handles migration continuity.
2. **Auth:** Add API key or JWT layer in Sprint 5+ if a mobile client or third-party
   integration is needed. Cookie auth remains for browser sessions.
3. **File uploads:** Move POD documents to S3-compatible storage when multi-instance
   deployment is required.
4. **AI layer (Sprint 5):** Read-only decision support (delay hints, anomaly summaries)
   sitting behind a feature flag; no autonomous writes.
5. **Frontend:** React consumer activates against stable API v1 contracts once Sprint 4
   write-flow hardening is complete.
