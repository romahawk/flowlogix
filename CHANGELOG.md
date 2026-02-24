# Changelog

All notable changes to FlowLogix are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `docs/PRD.md` — full product requirements document with killer feature, MVP scope, risks
- `docs/ARCHITECTURE.md` — system design, data flow, key components, tradeoffs
- `docs/ROADMAP.md` — outcome-based roadmap (weekly DoDs, milestones, freeze list)
- `docs/DECISIONS_LOG.md` — ADR log with 7 entries covering all major architecture decisions
- `.github/pull_request_template.md` — structured PR template with checklist
- `.github/ISSUE_TEMPLATE/feature_request.md` — updated with acceptance criteria and demo artifact fields
- `CONTRIBUTING.md` — branch naming, commit rules, issue/PR discipline, daily loop
- `CHANGELOG.md` — this file

### Changed
- `README.md` — full rewrite: 30-sec pitch, tech stack table, quick start, project structure, roadmap link

---

## [0.2.0] — 2026-02-14 (Sprint 2 Baseline)

### Added
- React frontend scaffold (`frontend-react/`) with Vite + React 18
- Component inventory: `AppShell`, `OrdersToolbar`, `OrdersTable`, `Pagination`, `ErrorBanner`, `EmptyState`
- `src/lib/queryState.js` — URL-synced query state for orders page
- `docs/ux-ui-spec.md` — UX principles, filter/sort contract, RBAC-driven UI behavior
- Sprint 2 summary doc in `docs/SPRINTS/`

### Changed
- Dashboard pagination default set to 10 rows; quantity formatting normalized
- Timeline: centered legend in controls row; sticky week-number row (`W1..W52`)
- Roadmap updated: legacy-first strategy; React path frozen

---

## [0.1.0] — 2025-Q4 (Sprint 1 — API v1 Hardened)

### Added
- `GET /api/v1/orders` — paginated, RBAC-scoped, deterministically sorted order list
- `GET /api/v1/auth/me` — current user identity for frontend auth bootstrap
- Strict query validation with 400 responses and structured JSON error envelopes
- `trace_id` on all API responses
- ISO 8601 date normalization in API output
- JSON 401 for unauthenticated API requests (no HTML redirect)
- Demo mode: auto-seed, auto-login, read-only guard
- `docs/adr/` — ADRs 0001–0005
- `docs/api/api-v1.md` — API contract stub
- `docs/architecture/` — architecture overview stub

### Changed
- Legacy Flask dashboard preserved as production path
- Alembic migrations formalized via Flask-Migrate
