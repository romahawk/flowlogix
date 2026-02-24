# Contributing to FlowLogix

This document covers the daily build discipline for this project.
It exists so every PR is readable, every change is traceable, and the repo
functions as proof-of-work — not just a code dump.

---

## Branch Naming

```
<type>/<short-description>
```

| Type | Use for |
|------|---------|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `chore/` | Maintenance, deps, config |
| `docs/` | Documentation only |
| `refactor/` | Code restructuring without behavior change |

Examples:
```
feature/api-v1-auth-login
fix/timeline-sticky-row-resize
chore/prune-requirements
docs/prd-architecture-roadmap
```

Rules:
- Branch from `main` (or `master`).
- Keep branches short-lived — one issue per branch.
- Avoid force-push on shared branches.

---

## Commit Message Rules

Format: `<type>(<scope>): <short description>`

```
feat(api): add POST /api/v1/auth/login endpoint
fix(dashboard): restore sticky week row on viewport resize
chore(deps): remove unused streamlit and scipy from requirements
docs(adr): add ADR-0007 retroactive OS adoption
refactor(js): extract api module from dashboard.js
test(api): add smoke tests for GET /api/v1/orders
```

Rules:
- Use imperative mood in the description ("add", not "added" or "adds").
- Keep the subject line under 72 characters.
- Reference the issue in the body if the commit resolves one: `Closes #12`.
- No emoji in commit messages unless the project standard changes.

---

## Issue Discipline

1. Every change starts with a GitHub Issue.
2. Use the correct template:
   - **Bug Report** — something broken
   - **Feature Request** — new behavior
   - **User Story** — user-facing requirement
3. Every issue must have:
   - A clear title
   - Acceptance criteria (specific, testable)
   - A label (`bug`, `feature`, `chore`, `docs`)
4. Assign the issue to yourself before starting work.

---

## PR Discipline

1. One PR per issue. PR title matches issue title.
2. Use the PR template — fill every section.
3. Link to the issue: `Closes #N` in the PR body.
4. Every PR must include a **demo artifact** (screenshot or test output).
5. Self-review your own diff before requesting merge:
   - No debug prints or commented-out code
   - No secrets or real credentials
   - No unrelated changes snuck in
6. Squash or rebase before merging to keep `main` history clean.

---

## Definition of Done (per issue)

- [ ] Acceptance criteria from the issue are met
- [ ] No regressions in existing manual flows
- [ ] Demo mode still works (auto-login, read-only guard)
- [ ] Relevant docs updated (API contract, ADR, roadmap if scope changed)
- [ ] Demo artifact attached to PR

---

## Daily Loop (Solo Discipline)

1. Review open issues — pick the highest-priority unblocked one.
2. Create or assign the issue to yourself.
3. Create a branch: `feature/your-description`.
4. Implement in small, atomic commits.
5. Open a PR referencing the issue.
6. Fill the PR template; attach a demo artifact.
7. Self-review the diff.
8. Merge to `main`.
9. Close the issue.
10. Update `CHANGELOG.md` if the change is user-visible.

---

## Local Setup Reminder

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade
python run.py
```

Run smoke tests (once added):
```bash
pytest tests/ -v
```
