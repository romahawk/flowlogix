# FlowLogix — Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 2026-02-24
**Status:** Active
**Owner:** Solo founder / engineering lead

---

## Problem

Small logistics operators and solo supply-chain managers track orders, warehouse stock,
and deliveries across spreadsheets, email threads, and ad-hoc tools. They have no single
authoritative view of where each shipment is, who owns it, or when it is due. Status
information drifts between people and tools, creating missed deliveries and reactive
firefighting instead of proactive management.

---

## Target User

**Primary:** Solo logistics operator or small-team supply-chain manager (1–10 people)
who manages 20–200 active orders simultaneously, needs role-scoped access (viewer vs.
admin), and works primarily at a desktop browser.

**Secondary:** A portfolio reviewer / prospective employer evaluating production-grade
engineering discipline, API design, and frontend-backend separation.

---

## Core Loop

1. **Log** — Create or import an order with all transit fields (ETD, ETA, ATA, status).
2. **Track** — Monitor orders in the dashboard table with real-time filters (status,
   year, buyer, transport).
3. **Visualize** — Use the timeline chart to see delivery cadence across weeks.
4. **Action** — Advance order stage: Orders → Warehouse → Delivered.
5. **Review** — Inspect activity logs and archived orders for audit and reporting.

---

## Killer Feature

**One deterministic dashboard that shows every order's transit state,
filtered and sorted server-side, with full RBAC safety — no spreadsheet required.**

---

## MVP Scope

- User authentication (login/logout) with session cookies.
- RBAC: Admin (full CRUD) and Viewer (read-only) roles.
- Orders list: paginated, filterable, sortable — driven by API v1.
- Timeline chart: visual delivery cadence synced to table filters.
- Warehouse stage: post-arrival stock management.
- Delivered stage: finalized shipment history.
- Activity log: audit trail of mutating actions.
- Demo mode: auto-seeded, read-only, public-safe.
- One-command local setup (venv → migrate → run).
- Gunicorn-ready deployment (Procfile, `wsgi.py`).

---

## Non-Goals (Current Phase)

- Full frontend rewrite to React (experimental; not the production path).
- External ERP/WMS integrations.
- Email/SMS/chat notification workflows.
- Multi-tenant billing or subscription management.
- Autonomous AI actions or write-capable AI suggestions.
- Mobile-first layout (desktop-first; mobile read support only).

---

## Acceptance Criteria for MVP

| # | Criterion |
|---|-----------|
| 1 | `GET /api/v1/orders` returns paginated, RBAC-scoped, deterministically sorted results with strict query validation. |
| 2 | `GET /api/v1/auth/me` returns current user identity and role without HTML redirect for API clients. |
| 3 | Dashboard table and timeline chart reflect identical filter/sort state. |
| 4 | Viewer role sees no mutating controls in the UI. |
| 5 | Demo mode auto-seeds on empty DB, auto-logs in as admin, and blocks all writes. |
| 6 | `flask db upgrade && python run.py` produces a working app from a clean clone. |
| 7 | All API errors return structured JSON with `trace_id`. |
| 8 | Gunicorn starts successfully via `Procfile`. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Monolithic `dashboard.js` (1007 lines) causes regressions during modularization | High | Medium | Extract modules incrementally with integration smoke tests before each PR. |
| Date/quantity fields stored as strings enable silent data corruption | Medium | High | Add migration to normalize key fields; add validation at model layer. |
| `requirements.txt` includes unused heavy deps (streamlit, scipy, selenium) | Medium | Low | Audit and prune in a dedicated chore PR. |
| React path and legacy path diverge without a clear cut-over decision | Medium | Medium | Freeze React migration until Sprint 5; document the decision in ADR. |
| No automated tests means regressions are invisible | High | High | Add smoke tests for API v1 endpoints in Sprint 3. |
| `.env.example` exposes an actual secret key value | High | Medium | Replace with placeholder before any public deploy. |
