# FlowLogix Roadmap

## North Star
API-first operations platform with a modernized legacy Flask UI, deterministic role-safe data access, and read-only AI decision support added later under strict governance.

## Strategy Update (2026)
- Primary UI path is now legacy-first: Flask templates + modular vanilla JS/CSS.
- React remains optional/experimental and is not the migration target.
- Backend API contracts stay authoritative and continue to drive deterministic behavior.

## Completed: Sprint 1 (API v1 Hardened)
- Delivered `GET /api/v1/orders` with RBAC, strict validation, pagination, filtering, and deterministic sorting.
- Delivered `GET /api/v1/auth/me` for frontend auth bootstrap.
- Added JSON-native API error behavior and normalized date output for frontend consistency.
- Preserved legacy UI while introducing API-first architecture incrementally.

## Current: Sprint 2 (Legacy Modernization Baseline)
### Scope
- Keep Orders and Timeline in legacy dashboard as the production path.
- Align table behavior with API query semantics (pagination, filtering, sorting).
- Improve timeline UX in legacy UI:
  - centered legend in top controls row
  - sticky week-number row (`W1..W52`) above chart
- Preserve existing backend route compatibility and operational workflows.

### Acceptance Criteria
- Legacy Orders table behavior remains deterministic and API-aligned.
- Timeline controls and sticky week row are stable across viewport resize.
- No regressions in add/edit/delete/move delivery flows.
- Existing Flask routes remain primary and stable.

## Next: Sprint 3 (Legacy JS/CSS Modularization)
### Scope
- Split `app/static/js/dashboard.js` into focused modules:
  - api/data loading
  - table/pagination
  - timeline rendering
  - form/actions
- Isolate timeline-specific styles from global `style.css` into scoped sections/files.
- Reduce encoding/mojibake debt and normalize text/labels to clean UTF-8-safe strings.

### Risks
- Regression risk during extraction from monolithic JS.
- Hidden coupling between template markup and JS selectors.
- CSS cascade side effects when splitting shared styles.

## Sprint 4 (Write Flow Hardening + RBAC UI Consistency)
### Scope
- Harden legacy write flows with clearer error handling and state feedback.
- Ensure UI action visibility exactly mirrors backend role permissions.
- Add integration checks around role-scoped actions and transitions.

### Risks
- Authorization drift between UI affordances and backend enforcement.
- Data integrity regressions without strict validation and idempotent action handling.
- Auditability gaps if mutating actions are not consistently logged.

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
- Legacy-first UI keeps delivery velocity high and avoids migration churn.
- Server-side sorting/filtering remains the deterministic, RBAC-safe source of truth.
- Strict `400` validation remains to prevent silent coercion and ambiguous UI behavior.

## Demo Checklist
- Seed data available and deterministic enough for repeatable demo flows.
- Demo user prepared with known role and credentials.
- Capture screenshots:
  - Orders table with filters + pagination.
  - Timeline with centered legend + sticky week row.
  - API validation error state (`400`) surfaced in UI.
  - Role-scoped view differences (Viewer vs Admin where available).
- Verify `/api/v1/orders` and `/api/v1/auth/me` in a fresh local run.

## Out of Scope (Current Phase)
- Full frontend rewrite/migration to React.
- External ERP/WMS integrations.
- Notification workflows (email/SMS/chat).
- Multi-tenant billing and subscription management.
- Autonomous AI actions.
