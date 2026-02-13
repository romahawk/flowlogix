# FlowLogix UX/UI Spec (Sprint 2-3)

## UX Principles
- Single source of truth: API response + URL query state define rendered state.
- Deterministic views: identical URL/query yields identical table and timeline output.
- Fast scanning: prioritize dense, readable tabular layout for operations users.
- Role clarity: actions and visibility reflect backend RBAC policy with no hidden privilege escalation.

## Information Architecture
### Current and Planned Pages
- Login (legacy Flask): existing auth entry point.
- Orders (React, Sprint 2): primary operational page and first migration target.
- Warehouse (React, phased): post-arrival inventory stage.
- Delivered (later): finalized shipments and historical review.
- Users (admin): user and role management.
- Activity Logs (later): audit and operational event trace.

## Orders Page Spec (Sprint 2)
### Header
- App branding + primary nav.
- Signed-in user identity + role badge.
- Theme toggle.

### Filters
- `filter[transit_status]`
- `filter[year]`
- `filter[q]`
- `filter[buyer]`
- `filter[responsible]`
- `filter[transport]`

### Table Behaviors
- Sort is server-driven via `sort` query key.
- Pagination is server-driven via `page` and `per_page`.
- Loading skeleton shown during fetch transitions.
- Empty state shown when `data=[]` for current filters.
- Error banner for API/network/auth/validation failures.

### URL-Synced Query State
Required query keys:
- `page` (default `1`)
- `per_page` (default `25`)
- `sort` (default `eta:desc,etd:desc,order_date:desc,id:desc`)
Optional filter keys:
- `filter[transit_status]`
- `filter[year]`
- `filter[q]`
- `filter[buyer]`
- `filter[responsible]`
- `filter[transport]`

Rules:
- UI controls always reflect URL state.
- Any filter/sort change resets `page=1`.
- Invalid query composition shows API validation errors from `400` response.

## Timeline Page Spec (Sprint 3)
- Timeline must consume the same filtered/sorted dataset contract as table.
- No drift allowed between timeline ordering and table ordering.
- Interaction rules:
  - Hover timeline item highlights corresponding table row.
  - Hover table row highlights corresponding timeline item.
  - Click on either side pins shared highlight/focus state.

## RBAC-Driven UI Behavior
- Viewer: read-only list access, no mutating controls rendered.
- Admin: management controls available where backed by API permissions.
- Other roles: scoped visibility/actions based on backend-enforced role policy.
- UI role checks are advisory; backend authorization is authoritative.

## Accessibility and Responsiveness Baseline
- Desktop-first layout, mobile acceptable for read-and-filter tasks.
- Minimum keyboard reachability for filters, table navigation, and pagination controls.
- Color contrast and status indicators must not rely on color alone.
- Error messages must be clear, concise, and screen-reader friendly.

## Component Inventory (High-Level)
- `AppShell`
- `OrdersToolbar`
- `OrdersTable`
- `Pagination`
- `ErrorBanner`
- `EmptyState`

## Non-Goals
- Pixel-perfect visual design parity during migration.
- Full design-system migration in Sprint 2-3.
- Heavy animation or motion-rich interactions.
