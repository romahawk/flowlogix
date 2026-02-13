# Sprint 1 - API v1 Orders (Complete)

## Goal
Establish a production-grade API-first backend foundation for FlowLogix that React can consume without coupling to server-rendered templates.

## Delivered
- `GET /api/v1/orders` with RBAC-safe scope control.
- Server-side pagination: `page`, `per_page`.
- Server-side filtering: `filter[transit_status]`, `filter[year]`, `filter[q]`, `filter[buyer]`, `filter[responsible]`, `filter[transport]`.
- Stable, deterministic multi-field sorting with tie-breaker `id:desc`.
- Strict query validation with structured `400` validation responses.
- JSON auth behavior for API routes (no HTML redirect payloads).
- `GET /api/v1/auth/me` for frontend bootstrap.

## Quality Guarantees
- Deterministic ordering for identical query inputs.
- Strict validation at API boundary (fail fast, no silent coercion).
- Role-safe server-side data scope.

## Deferred Intentionally
- Timeline UI.
- Write endpoints and bulk operations.
- Cursor pagination and search indexing.

## Exit Criteria Met
- API v1 read endpoints stable and portfolio-demo ready.
- React foundation work can start with low backend rework risk.
