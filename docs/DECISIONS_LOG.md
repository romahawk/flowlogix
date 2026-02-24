# FlowLogix — Architecture Decision Records (ADR Log)

Lightweight ADR log. Each entry captures: context, decision, status, and consequences.
Full ADR stubs live in `docs/adr/`.

---

## ADR-0001 — API-First Migration Strategy

**Date:** 2025-Q4
**Status:** Accepted

**Context:**
The original app was a fully server-rendered Flask/Jinja2 dashboard. A React migration
was considered to modernize the frontend, but a full rewrite carries high regression risk
and delivery cost for a solo maintainer.

**Decision:**
Formalize a JSON API layer (v1) incrementally while keeping the Jinja2 UI as the
production path. API contracts become the authoritative source of truth for data shape,
validation, and RBAC semantics.

**Consequences:**
- (+) Legacy UI remains stable; no big-bang rewrite risk.
- (+) API contracts are reusable by future React consumer or external clients.
- (-) Two UI paths (legacy + React) must be kept in sync until a cut-over decision.
- (-) Backend carries both Jinja template routes and JSON API blueprints simultaneously.

---

## ADR-0002 — Strict Query Validation (400 on Bad Params)

**Date:** 2025-Q4
**Status:** Accepted

**Context:**
Early iterations silently coerced or ignored invalid query parameters (e.g., bad sort
fields, unknown filter keys), making it impossible to distinguish "no results" from
"invalid query." This caused hidden bugs in the UI.

**Decision:**
All API v1 query parameters are validated strictly. Unknown sort fields, invalid filter
keys, or out-of-range pagination values return `400 Bad Request` with a structured error
envelope including `trace_id`.

**Consequences:**
- (+) Eliminates silent coercion bugs; client must send valid queries.
- (+) Error envelope pattern is consistent and machine-readable.
- (-) UI must handle 400 responses explicitly and surface them to the user.
- (-) Any future query param addition requires schema update and migration path.

---

## ADR-0003 — Server-Side Sorting and Filtering

**Date:** 2025-Q4
**Status:** Accepted

**Context:**
Client-side sorting was considered (JavaScript sort after full dataset fetch). This
creates data leakage risk (sending more records than the user's role permits) and
produces non-deterministic sort when records share key values.

**Decision:**
All sort, filter, and pagination operations are performed server-side by SQLAlchemy
queries. The client sends declarative query state (URL params); the backend is
authoritative.

**Consequences:**
- (+) No data leakage: only permitted records are returned.
- (+) Deterministic sort even with ties (stable multi-column sort).
- (+) URL state is reproducible: same URL → same result.
- (-) Every sort/filter interaction is a network round-trip.
- (-) More complex query-building logic on the backend.

---

## ADR-0004 — Session Cookie Authentication (No JWT)

**Date:** 2025-Q4
**Status:** Accepted

**Context:**
JWT was considered for stateless API auth. At current scale (single-user demo, small
team), the overhead of token management, refresh flows, and secure storage is not
justified.

**Decision:**
Flask-Login session cookies are used for both the legacy UI and API v1. The API
returns JSON 401 (not HTML redirect) for unauthenticated requests.

**Consequences:**
- (+) Simple, battle-tested, zero extra infrastructure.
- (+) Works seamlessly with the existing Jinja2 session model.
- (-) Not suitable for stateless horizontal scaling or mobile clients.
- (-) Requires a dedicated API key / JWT path in Sprint 5+ for non-browser consumers.

---

## ADR-0005 — Date Normalization to ISO 8601 in API Output

**Date:** 2025-Q4
**Status:** Accepted

**Context:**
Date fields in the database are stored as `String(10)` in mixed formats (`YYYY-MM-DD`,
`DD.MM.YY`, `DD.MM.YYYY`). The legacy UI handled this with a `format_date` Jinja
filter. API consumers need a consistent, parseable date format.

**Decision:**
API v1 normalizes all date output to ISO 8601 (`YYYY-MM-DD`) in the response envelope.
Storage format inconsistencies are handled at the serialization layer, not in the
database.

**Consequences:**
- (+) API consumers receive consistent, machine-readable dates.
- (-) Does not fix the underlying storage debt (strings instead of Date columns).
- (-) Normalization logic must be maintained in the serialization layer until a DB
  migration normalizes the storage format (planned, not yet scheduled).

---

## ADR-0006 — Legacy-First UI Path (React Migration Frozen)

**Date:** 2026-02-24
**Status:** Accepted

**Context:**
Sprint 2 docs originally framed a React migration as the forward path. The roadmap was
subsequently updated to "legacy-first." The React codebase (`frontend-react/`) exists
but is incomplete and not the production path.

**Decision:**
The Jinja2 + vanilla JS legacy UI is the production path through at least Sprint 4.
React migration is explicitly frozen and will not receive production features until API
v1 write endpoints and Sprint 4 hardening are complete. The React codebase remains in
`frontend-react/` as an experimental artifact.

**Consequences:**
- (+) Eliminates parallel-path maintenance burden during active hardening sprints.
- (+) All UX improvements land in the legacy UI where users actually work.
- (-) React developers evaluating the codebase may see an incomplete migration.
- (-) Cut-over timeline remains undefined; needs a formal decision before Sprint 5.

---

## ADR-0007 — Retroactive AI Production OS Adoption

**Date:** 2026-02-24
**Status:** Accepted

**Context:**
Repository reached Sprint 2 organically without a formal product/engineering framework.
Doc coverage was thin (API doc stubs, near-empty architecture doc, no PRD). Issue and PR
discipline existed (templates present, feature branches in use) but lacked explicit
Definitions of Done and outcome-based roadmap structure.

**Decision:**
Retroactively adopt the AI Production OS v1 framework. All new docs (PRD, ARCHITECTURE,
ROADMAP, DECISIONS_LOG) are written to this standard. Future sprints follow the
Issue → PR → Deploy loop with explicit DoD and demo artifacts per week.

**Consequences:**
- (+) Repo becomes proof-of-work credible: reviewable, demo-ready, disciplined.
- (+) Solo founder has a reusable execution structure for future projects.
- (-) Some docs are retroactive approximations; they will drift from reality if not
  maintained. Commit to reviewing docs at the start of each sprint.
