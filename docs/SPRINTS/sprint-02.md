# Sprint 2 - React Foundation (In Progress)

## Goal
Deliver the first React client vertical slice for Orders while preserving backend API-first guarantees.

## Scope
- React app shell with user/role header.
- Auth bootstrap via `GET /api/v1/auth/me`.
- Orders page consuming `GET /api/v1/orders`.
- URL-synced query state for `page`, `per_page`, `sort`, and filter keys.
- Loading, empty, validation-error, and unauthorized states.

## Implemented in this increment
- `frontend-react/` app scaffolded with Vite + React.
- Component inventory created:
  - `AppShell`
  - `OrdersToolbar`
  - `OrdersTable`
  - `Pagination`
  - `ErrorBanner`
  - `EmptyState`
- Deterministic query-state logic implemented in `src/lib/queryState.js`.
- API client implemented with credentials and structured error handling.

## Remaining to complete Sprint 2
- Add role-aware action placeholders (Viewer/Admin visibility framing).
- Add transport/status option dictionaries sourced from API metadata (when available).
- Add basic smoke tests for query serialization and API error rendering.
- Wire route deployment strategy (standalone host vs Flask static serving).

## Exit Criteria
- Orders table behavior remains fully server-driven.
- URL reload reproduces the same page state.
- Invalid query composition surfaces API 400 details in UI.
