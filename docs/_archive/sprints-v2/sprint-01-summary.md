# Sprint 01 — API v1 (Orders)

## Goal
Establish a **production-grade, API-first backend foundation** for FlowLogix, decoupled from Flask templates, suitable for React consumption and portfolio demonstration.

Primary focus:
- Deterministic data access
- Clear API contract
- RBAC correctness
- Demo-ready stability

---

## Scope (Delivered)

### Core Endpoint
- `GET /api/v1/orders`

### Features
- Role-Based Access Control (RBAC)
- Server-side pagination (`page`, `per_page`)
- Server-side filtering:
  - `filter[transit_status]`
  - `filter[year]` (ANY-date legacy semantics)
  - `filter[q]` (search)
  - `filter[buyer]`, `filter[responsible]`, `filter[transport]`
- Stable multi-field sorting with deterministic tie-breaker (`id:desc`)
- Consistent API response envelope:
  ```json
  { "data": [], "meta": {}, "trace_id": "uuid" }
  ```
- Strict query validation with structured **400 Validation Errors**
- JSON-only auth errors (no HTML redirects)
- Demo seed data + demo login flow

---

## API Quality Guarantees

- **Deterministic ordering** — identical requests always return identical order
- **Strict validation** — invalid query parameters fail fast with 400
- **RBAC-safe** — data scope enforced server-side
- **Frontend-safe contract** — React can rely on API behavior

---

## Tradeoffs & Decisions

### Chosen
- Python-side sorting and year filtering (due to legacy string-based dates)
- Tolerant date parsing, strict output normalization (ISO for real date fields)
- Validation at API boundary (instead of silent coercion)

### Deferred (Intentionally)
- Cursor-based pagination
- Full-text search indexing
- Bulk write endpoints (POST/PUT)
- Timeline visualization
- AI decision-support features

---

## Testing

- Authenticated API tested via `curl`
- Positive and negative paths validated:
  - Invalid filters → 400
  - Invalid sort fields → 400
  - Invalid pagination → 400
- Demo environment verified

---

## Outcome

Sprint 01 delivers a **clean, production-grade API foundation** that:
- Eliminates UI–data coupling
- Enables a React-based frontend without backend rewrites
- Serves as a strong portfolio artifact demonstrating backend engineering maturity

---

## Next Sprint

**Sprint 02 — React Foundation**
- React + Tailwind shell
- Auth bootstrap via `/api/v1/auth/me`
- Orders table consuming `/api/v1/orders`
- No timeline yet (planned for Sprint 03)
