# FlowLogix Roadmap

## North Star
API-first operations platform with a React UI, deterministic role-safe data access, and read-only AI decision support added later under strict governance.

## Completed: Sprint 1 (API v1 Hardened)
- Delivered `GET /api/v1/orders` with RBAC, strict validation, pagination, filtering, and deterministic sorting.
- Delivered `GET /api/v1/auth/me` for frontend auth bootstrap.
- Added JSON-native API error behavior and normalized date output for frontend consistency.
- Preserved legacy UI while introducing API-first architecture incrementally.

## Current: Sprint 2 (React Foundation)
### Scope
- Build React app shell and authenticated session bootstrap using `/api/v1/auth/me`.
- Implement Orders page first (table-centric) consuming `/api/v1/orders`.
- Add URL-synced query state for filter, sort, and pagination.
- Add resilient states: loading, empty, validation-error, unauthorized.

### Acceptance Criteria
- Orders table renders paginated server data with parity to API query semantics.
- URL reload reproduces the same table state deterministically.
- Invalid query inputs surface actionable validation details from API `400` payloads.
- No regression to Flask template routes.

## Next: Sprint 3 (Timeline + Visualization)
### Scope
- Add timeline visualization bound to the same dataset contract as table view.
- Enable row-to-timeline and timeline-to-row interaction sync.
- Preserve one query state model for both table and timeline.

### Risks
- Drift risk if timeline applies client-only transforms not used by table.
- Performance risk on larger pages if visualization redraw is not throttled.
- UX risk if timeline interactions hide source-of-truth table state.

## Sprint 4 (Write Flows + RBAC UI Controls)
### Scope
- Add create/update flows for selected entities via API write endpoints.
- Introduce role-aware action controls in React UI.
- Add optimistic/confirmed update patterns with server truth reconciliation.

### Risks
- Authorization bugs if UI role checks diverge from backend RBAC enforcement.
- Data integrity regressions without idempotency and input constraints.
- Auditability gaps if write actions are not consistently logged.

## Sprint 5 (AI Read-Only Decision Support + Hardening)
### Scope
- Add read-only AI recommendations (delay/risk hints, anomaly summaries).
- Introduce audit logs and traceability for AI-assisted outputs.
- Complete deployment hardening: environment separation, monitoring, backup/restore rehearsal.

### Guardrails
- AI remains read-only: no autonomous writes or workflow mutation.
- Every AI output references visible source fields and confidence framing.
- Human decision remains authoritative; AI suggestions are advisory.

## Explicit Tradeoffs
- Server-side sorting/filtering chosen to guarantee deterministic, RBAC-safe, reusable contracts across clients.
- Strict `400` validation chosen to prevent silent coercion and ambiguous UI behavior.
- Timeline deferred to Sprint 3 to first stabilize data contracts and table UX baseline in Sprint 2.

## Demo Checklist
- Seed data available and deterministic enough for repeatable demo flows.
- Demo user prepared with known role and credentials.
- Capture screenshots:
  - Orders table with filters + pagination.
  - API validation error state (`400`) surfaced in UI.
  - Role-scoped view differences (Viewer vs Admin where available).
- Verify `/api/v1/orders` and `/api/v1/auth/me` in a fresh local run.

## Out of Scope (Current Migration)
- External ERP/WMS integrations.
- Notification workflows (email/SMS/chat).
- Multi-tenant billing and subscription management.
- Full design-system migration.
- Autonomous AI actions.
