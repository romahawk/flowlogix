# CLAUDE.md — AI Session Rules for FlowLogix

**Stack:** Python 3.11 · Flask 3 · SQLAlchemy · Jinja2 · Vanilla JS · Tailwind CSS (CDN)
**This file is authoritative.** Read it completely before writing any code.

---

## 1. AI Role Boundary

Claude is a **code executor and research assistant**, not a decision-maker.

| Decision type | Who decides |
|---------------|-------------|
| Roadmap priorities, sprint goals | **User only** |
| Which issue to work on next | **User only** |
| Architecture changes (new deps, DB swap, auth scheme) | **User only — requires ADR** |
| Whether to merge or close a PR/issue | **User only** |
| Scope changes mid-task | **User only — stop and ask** |
| Implementation of a scoped, assigned issue | Claude (within the agreed spec) |
| Writing tests, docs, and refactors inside a defined issue | Claude |

**If in doubt, stop and ask.** Do not infer scope. Do not expand scope. Do not close issues unilaterally.

---

## 2. Pre-Commit Gates (Both Must Pass)

Before every commit, run these two commands. Do not commit if either fails.

```bash
# 1. Lint — must exit 0
ruff check .

# 2. Tests — must exit 0
pytest tests/ -v
```

If `ruff` is not installed: `pip install ruff`
If `tests/` does not exist yet, note it in the PR and create a placeholder `tests/test_smoke.py`.

---

## 3. Anti-Patterns — Refuse These

| # | Anti-pattern | Why |
|---|--------------|-----|
| A1 | Committing directly to `main` or `master` | All work goes through feature branches + PRs |
| A2 | Skipping the pre-commit gates (ruff + pytest) | Gates exist to catch regressions before merge |
| A3 | Adding a new dependency without updating `requirements.txt` | Causes silent breakage on fresh installs |
| A4 | Hardcoding secrets, credentials, or real URLs | Security; use `.env` and `.env.example` |
| A5 | Expanding scope beyond the assigned issue | Scope creep breaks sprint accountability |
| A6 | Making roadmap or priority decisions unilaterally | User owns the roadmap |
| A7 | Touching the `frontend-react/` directory | Frozen until Sprint 5 — see ADR-0006 |
| A8 | Writing to the DB from an AI suggestion (Sprint 5+) | AI layer is read-only; no autonomous writes |
| A9 | Removing demo mode or auto-login guards | Demo mode is a core portfolio requirement |
| A10 | Force-pushing to a shared branch | Use `--force-with-lease` only if agreed with user |
| A11 | Committing without a `Closes #N` reference when an issue exists | All changes must trace to an issue |
| A12 | Leaving `print()` debug statements in committed code | Clean commits only |

---

## 4. Commit Discipline

Format: `type(scope): short description` (imperative mood, ≤72 chars)

Valid types: `feat` `fix` `chore` `docs` `refactor` `test`

Commit body must include `Closes #N` when resolving an issue.

```
feat(api): add POST /api/v1/auth/login endpoint

Closes #9
```

Max diff size per commit: **200 lines** (insertions + deletions). Split larger changes into atomic commits.

---

## 5. Branch Naming

```
feature/issue-{N}-short-description
fix/issue-{N}-short-description
chore/issue-{N}-short-description
docs/issue-{N}-short-description
refactor/issue-{N}-short-description
test/issue-{N}-short-description
claude/*   (Claude Code automation branches)
```

Branch from `main`. One issue per branch.

---

## 6. Stack Rules

- **Do not introduce** new Python packages without user approval + `requirements.txt` update.
- **Do not add** a second CSS framework. Tailwind (CDN) is the only styling system.
- **Do not add** `@mui`, `emotion`, `bootstrap`, or `styled-components` (even in `frontend-react/`).
- **SQLite** stays until the user explicitly authorizes a Postgres migration.
- **No JWT or API keys** introduced without an ADR.
- All API responses must include `trace_id`. See `app/api/v1/errors.py`.

---

## 7. Key Paths (read before touching related code)

| Concern | Path |
|---------|------|
| App factory + demo mode | `app/__init__.py` |
| RBAC decorator | `app/decorators.py` |
| API v1 endpoints | `app/api/v1/` |
| Request/response schemas | `app/api/v1/schemas.py` |
| JSON error envelopes | `app/api/v1/errors.py` |
| Dashboard JS (monolith — handle with care) | `app/static/js/dashboard.js` |
| Seeder (demo-safe) | `app/seed_boot.py` |
| Migrations | `migrations/` |
| API contract doc | `docs/api/api-v1.md` |
| Architecture decisions | `docs/adr/` |

---

## 8. Definition of Done (per issue)

- [ ] Acceptance criteria from the GitHub issue are fully met
- [ ] `ruff check .` exits 0
- [ ] `pytest tests/ -v` exits 0 (or new tests added for new behavior)
- [ ] No regressions: existing routes, API endpoints, and demo mode still work
- [ ] `Closes #N` in the commit body or PR body
- [ ] Demo artifact attached to PR (screenshot or terminal output)
- [ ] `CHANGELOG.md` updated if the change is user-visible
- [ ] `docs/` updated if API contract, architecture, or a decision changed
