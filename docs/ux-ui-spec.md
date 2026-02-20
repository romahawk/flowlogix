# FlowLogix UX/UI Spec (Legacy-First, Sprint 2-4)

## UX Principles
- Single source of truth: API response + URL/query state define rendered state.
- Deterministic views: identical query inputs yield identical table and timeline output.
- Fast scanning: prioritize dense, readable tabular layout for operations users.
- Role clarity: actions and visibility reflect backend RBAC policy with no hidden privilege escalation.
- Incremental modernization: improve the existing legacy UI in-place before considering rewrites.

## Information Architecture
### Current and Planned Pages (Legacy Flask UI)
- Login: existing auth entry point.
- Dashboard Orders + Timeline: primary operational interface.
- Warehouse: post-arrival inventory stage.
- Delivered: finalized shipments and historical review.
- Users (admin): user and role management.
- Activity Logs: audit and operational event trace.

## Orders + Timeline Page Spec
### Header
- App branding + primary navigation.
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
- Any filter/sort change resets page to first page.
- Empty state shown when no rows match current filters.
- Validation/API errors surfaced clearly from backend response.

### Timeline Behaviors (Legacy Chart)
- Timeline consumes the same filtered/sorted dataset contract as table view.
- No drift allowed between timeline ordering and table ordering.
- Legend is centered in the top timeline controls row.
- Week-number strip (`W1..W52`) is sticky at the top of timeline container.
- Year selector remains visible in timeline controls row.

## Query and Determinism Contract
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
- UI controls reflect current query state.
- Invalid query composition surfaces backend `400` validation details.
- Backend remains authoritative for sort/filter/pagination semantics.

## RBAC-Driven UI Behavior
- Viewer: read-only list access, no mutating controls rendered.
- Admin: management controls available where backed by API permissions.
- Other roles: scoped visibility/actions based on backend-enforced role policy.
- UI role checks are advisory; backend authorization is authoritative.

## Accessibility and Responsiveness Baseline
- Desktop-first layout; mobile supports read/filter workflows.
- Keyboard reachability for filters, table navigation, and pagination controls.
- Color/status communication does not rely on color alone.
- Error messages are concise and screen-reader friendly.

## Frontend Modernization Guidelines (Legacy)
- Prefer small, testable JS modules over monolithic scripts.
- Keep template IDs/data attributes stable when extracting modules.
- Scope timeline/table styles to reduce global cascade side effects.
- Preserve backward compatibility with Flask routes and forms.

## Non-Goals (Current Phase)
- Full UI rewrite to React.
- Pixel-perfect design-system migration.
- Heavy animation/motion-rich UI.
