# Sprint Backlog — FlowLogix

**Active Sprint:** Week 3 — Legacy JS Modularization
**Sprint goal:** Split `dashboard.js` into focused modules with no regressions in table or timeline behavior.
**Sprint dates:** 2026-03-03 → 2026-03-09

---

## Active Issues

### #10 — Extract `api/` module from `dashboard.js`
**Label:** feature | **Branch:** `feature/issue-10-extract-api-module`

Split all data-fetch and error-handling logic into `app/static/js/api/orders.js`.

**Acceptance criteria:**
- [ ] `dashboard.js` no longer contains `fetch(...)` calls directly — all API calls go through `api/orders.js`
- [ ] Error handling (network errors, non-200 responses) lives in the API module
- [ ] `dashboard.js` calls `api/orders.js` functions; no behavior change visible to the user
- [ ] `ruff check .` and `pytest tests/ -v` both pass after the change
- [ ] Manual smoke test: orders table loads, filters work, pagination works

---

### #11 — Extract `table/` module from `dashboard.js`
**Label:** feature | **Branch:** `feature/issue-11-extract-table-module`

Move pagination controls and row-render logic into `app/static/js/table/orders.js`.

**Acceptance criteria:**
- [ ] Table pagination (prev/next, page info display) controlled by `table/orders.js`
- [ ] Row render logic (status badges, quantity formatting) moved to the module
- [ ] `dashboard.js` calls module functions; no visual regression
- [ ] `ruff check .` and `pytest tests/ -v` both pass

---

### #12 — Extract `timeline/` module from `dashboard.js`
**Label:** feature | **Branch:** `feature/issue-12-extract-timeline-module`

Move chart render, week-strip, and legend logic into `app/static/js/timeline/chart.js`.

**Acceptance criteria:**
- [ ] `renderTimeline()`, `ensureTimelineWeekHeader()`, `syncTimelineWeekHeader()` all live in `timeline/chart.js`
- [ ] Sticky week row (`W1..W52`) still aligns correctly on viewport resize
- [ ] Overdue flashing border and delay toggle still function
- [ ] Centered legend visible and correct in both light and dark mode
- [ ] `ruff check .` and `pytest tests/ -v` both pass

---

### #13 — Scope timeline CSS out of global `style.css`
**Label:** chore | **Branch:** `chore/issue-13-scope-timeline-css`

Move all `.timeline-*` selectors from `app/static/css/style.css` into a dedicated `app/static/css/timeline.css`.

**Acceptance criteria:**
- [ ] `style.css` contains no `.timeline-*` rules
- [ ] `timeline.css` is loaded only on pages that render the timeline
- [ ] No visual regression on dashboard, orders, warehouse, or analytics pages
- [ ] `ruff check .` and `pytest tests/ -v` both pass

---

### #14 — Add integration smoke test: page loads, table renders, timeline renders
**Label:** chore | **Branch:** `chore/issue-14-smoke-tests`

Add a `tests/test_smoke.py` file with basic integration checks using Flask test client.

**Acceptance criteria:**
- [ ] `GET /` redirects to login or auto-logins in demo mode (200)
- [ ] `GET /dashboard` returns 200 and contains the string `orderTableBody`
- [ ] `GET /api/v1/orders?page=1&per_page=5` returns 200 with JSON `{data, pagination, trace_id}`
- [ ] `GET /api/v1/auth/me` returns 200 with `{id, username, role}`
- [ ] All tests pass with `pytest tests/ -v`

---

## Backlog (Next Sprint — Week 4: Write Flow Hardening)

| # | Title | Label |
|---|-------|-------|
| #15 | Audit all POST routes: consistent flash messages and redirects | chore |
| #16 | Viewer role sees zero mutating controls in all templates | bug |
| #17 | RBAC integration tests for order add/edit/delete by role | chore |
| #18 | Harden demo readonly guard: cover all write-capable routes | chore |

---

## Done This Sprint

*(Move issues here as they are merged to main)*

| # | Title | Merged |
|---|-------|--------|
| — | — | — |
