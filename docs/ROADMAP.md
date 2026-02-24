# FlowLogix — Roadmap

**Version:** 2.0 (Rebuilt 2026-02-24)
**Framework:** AI Production OS v1
**Strategy:** Legacy-first stabilization → API hardening → AI read layer

---

## North Star

A production-grade, portfolio-ready logistics operations platform:
deterministic order tracking, role-safe data access, clean API contracts,
and a demonstrable daily-build discipline visible in commit and PR history.

---

## Next 4 Weeks — Weekly Outcomes

### Week 1 — Foundation Credibility
**Outcome:** Repo is credible at a glance. A reviewer can clone, run, and navigate it in under 5 minutes.

| Issue | Title | Label |
|-------|-------|-------|
| #1 | Replace real secret in `.env.example` with placeholder | chore |
| #2 | Prune unused heavy dependencies from `requirements.txt` | chore |
| #3 | Add `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/DECISIONS_LOG.md` | docs |
| #4 | Add `.github/pull_request_template.md` and `CONTRIBUTING.md` | docs |
| #5 | Update `README.md`: 30-sec pitch, setup, stack badge, roadmap link | docs |

**Definition of Done:**
- [ ] `git clone` → `pip install` → `flask db upgrade` → `python run.py` succeeds with zero errors in a fresh venv.
- [ ] README renders cleanly on GitHub with working links.
- [ ] `.env.example` contains no real secrets.
- [ ] `docs/` has PRD, ARCHITECTURE, ROADMAP, DECISIONS_LOG.

**Demo artifact:** Screenshot of running dashboard with seeded demo data.

---

### Week 2 — API v1 Hardening + First Test Coverage
**Outcome:** API v1 is tested, documented, and behaves identically to its spec. First automated signal of code health.

| Issue | Title | Label |
|-------|-------|-------|
| #6 | Write smoke tests for `GET /api/v1/orders` (happy path + 400 cases) | chore |
| #7 | Write smoke tests for `GET /api/v1/auth/me` (authed + 401) | chore |
| #8 | Expand `docs/api/api-v1.md` with full parameter reference, response schema, error codes | docs |
| #9 | Add `POST /api/v1/auth/login` and `POST /api/v1/auth/logout` JSON endpoints | feature |

**Definition of Done:**
- [ ] `pytest tests/` passes with zero failures.
- [ ] API docs include every query param, response field, and error code.
- [ ] `/api/v1/auth/me` 401 response matches JSON envelope spec.

**Demo artifact:** `pytest` terminal output showing all tests green.

---

### Week 3 — Legacy JS Modularization (Sprint 3)
**Outcome:** `dashboard.js` split into focused modules; no regressions in table or timeline behavior.

| Issue | Title | Label |
|-------|-------|-------|
| #10 | Extract `api/` module from `dashboard.js` (data-fetch + error handling) | feature |
| #11 | Extract `table/` module (pagination controls, row render) | feature |
| #12 | Extract `timeline/` module (chart render, week-strip, legend) | feature |
| #13 | Scope timeline CSS out of global `style.css` | chore |
| #14 | Add integration smoke test: page loads, table renders, timeline renders | chore |

**Definition of Done:**
- [ ] `dashboard.js` reduced to an orchestrator under 200 lines.
- [ ] Each extracted module has a clear single responsibility.
- [ ] No regressions: add/edit/delete/move delivery flows pass manual smoke test.
- [ ] Timeline sticky week row and centered legend remain stable across viewport resize.

**Demo artifact:** Loom (or screenshot sequence) showing dashboard table + timeline working after modularization.

---

### Week 4 — Write Flow Hardening (Sprint 4)
**Outcome:** All mutating actions have clear error feedback, RBAC UI consistency, and are integration-tested.

| Issue | Title | Label |
|-------|-------|-------|
| #15 | Audit all POST routes: ensure consistent flash messages and redirect behavior | chore |
| #16 | Ensure Viewer role sees zero mutating controls in all templates | bug/chore |
| #17 | Add RBAC integration tests for order add/edit/delete by role | chore |
| #18 | Harden demo readonly guard: cover all write-capable routes | chore |

**Definition of Done:**
- [ ] Every mutating route returns a user-visible success or error message.
- [ ] Viewer-role session cannot reach any mutating URL (returns 403).
- [ ] Demo readonly guard tested against all POST/PUT/DELETE paths.

**Demo artifact:** Screenshot showing role-scoped view (Viewer vs Admin) side-by-side.

---

## Next 3 Months — Milestones

### Month 2 — Production Hardening

**Goal:** App is deployable to a real host, observable, and safe to share publicly.

| Milestone | Description |
|-----------|-------------|
| M1: Deploy to Render/Railway | `gunicorn` + environment variables, demo mode on, public URL |
| M2: Error observability | Structured logging on every 4xx/5xx; request `trace_id` in logs |
| M3: DB backup rehearsal | `flask db dump` + restore procedure documented in `docs/ops/` |
| M4: Performance baseline | p95 response time for `/api/v1/orders` under 200ms on demo data |

---

### Month 3 — AI Read Layer (Sprint 5)

**Goal:** Read-only AI decision support integrated under strict guardrails.

| Milestone | Description |
|-----------|-------------|
| M5: Delay risk hints | Flag orders where ETA is past and ATA is empty (rule-based first, LLM second) |
| M6: Anomaly summary | Daily digest: orders with status drift or missing fields |
| M7: AI audit log | Every AI suggestion stored with source fields and confidence framing |
| M8: Feature flag | AI layer behind `ENABLE_AI_HINTS=true` env flag; off by default |

**Guardrails (non-negotiable):**
- AI is read-only. No autonomous writes or workflow mutations.
- Every AI output references visible source fields.
- Human decision remains authoritative; AI suggestions are advisory only.

---

## Freeze List (Will Not Be Touched Until Month 3+)

- Full frontend migration to React (experimental path frozen).
- External ERP/WMS integrations.
- Multi-tenant architecture or subscription billing.
- Notification workflows (email, SMS, chat).
- Database migration away from SQLite (until concurrent write load justifies it).
- Autonomous AI actions of any kind.

---

## Completed

### Sprint 1 (API v1 Hardened) — Done
- `GET /api/v1/orders`: RBAC, strict validation, pagination, filtering, deterministic sort.
- `GET /api/v1/auth/me`: frontend auth bootstrap.
- JSON-native error behavior with `trace_id`.
- Normalized ISO date output.

### Sprint 2 (Legacy Modernization Baseline) — Partially Done
- Legacy Orders table: API-aligned pagination and filtering.
- Timeline: centered legend, sticky week row.
- React app scaffolded (experimental; frozen).
