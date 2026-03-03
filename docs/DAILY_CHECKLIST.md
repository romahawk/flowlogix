# Daily Checklist — FlowLogix

Run through this list at the start of each working session. It takes under 2 minutes.
The goal is zero surprises before you write a single line of code.

---

## Morning (Start of Session)

### 1. Environment
```bash
source .venv/bin/activate
pip install -r requirements.txt   # only if requirements.txt changed since last session
flask db upgrade                  # only if new migrations exist
```

### 2. Check Your Branch
```bash
git branch --show-current
# Must match: feature/issue-{N}-*, fix/issue-{N}-*, chore/issue-{N}-*, claude/*
# Must NOT be: main or master
```

### 3. Sync With Main
```bash
git fetch origin main
git log --oneline origin/main..HEAD   # see what's ahead
```

### 4. Run the Gates (Baseline — Must Be Green Before You Start)
```bash
ruff check .
pytest tests/ -v
```
**If either fails before you've touched anything: fix it first. Don't build on a broken base.**

### 5. Confirm the App Runs
```bash
python run.py
# Visit http://127.0.0.1:5000 — confirm auto-login and dashboard load
# Ctrl+C to stop
```

### 6. Confirm the Assigned Issue
- [ ] Issue is assigned to you on GitHub
- [ ] Acceptance criteria are clear and testable
- [ ] Branch name follows convention: `feature/issue-{N}-description`

---

## During Work

### Before Each Commit
```bash
ruff check .          # must exit 0
pytest tests/ -v      # must exit 0
git diff --stat HEAD  # confirm diff is ≤ 200 lines
```

Commit format:
```
type(scope): short description (≤72 chars)

Closes #N
```

### Scope Check (After Each Commit)
- [ ] This commit only addresses the assigned issue
- [ ] No unrelated files changed
- [ ] No new dependencies added without `requirements.txt` update

---

## End of Session

### 1. Run Gates One Last Time
```bash
ruff check .
pytest tests/ -v
```

### 2. Push Your Branch
```bash
git push -u origin $(git branch --show-current)
```

### 3. If the Issue Is Done — Open a PR
- [ ] PR title matches issue title
- [ ] `Closes #N` in the PR body
- [ ] PR template filled (What / Why / How / How to Test / Checklist / Demo Artifact)
- [ ] Screenshot or terminal output attached as demo artifact
- [ ] CHANGELOG.md updated if the change is user-visible

### 4. Update Sprint Backlog
- Move the issue to **Done This Sprint** in `docs/SPRINT_BACKLOG.md`
- Note the merge date

### 5. Pick Tomorrow's Issue
- Review `docs/SPRINT_BACKLOG.md` — pick the next unblocked issue
- Note it so you can start cleanly tomorrow

---

## Weekly (End of Sprint)

- [ ] All sprint issues merged to `main`
- [ ] `docs/SPRINT_BACKLOG.md` reset for the next sprint
- [ ] `CHANGELOG.md` entry added for any user-visible changes
- [ ] `docs/ROADMAP.md` Definition of Done checkboxes updated
- [ ] Retrospective note: what slowed you down this sprint?

---

## Quick Reference — Gate Commands

| Gate | Command | Pass condition |
|------|---------|----------------|
| Lint | `ruff check .` | Exit 0, no output |
| Tests | `pytest tests/ -v` | All tests pass |
| App starts | `python run.py` | No import errors, dashboard loads |
| DB up to date | `flask db upgrade` | "Nothing to migrate" or clean migration |
