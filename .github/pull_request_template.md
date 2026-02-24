## What

<!-- One sentence: what does this PR change? -->

## Why

<!-- Why is this change needed? Link to the issue: Closes #N -->

Closes #

## How

<!-- Brief description of implementation approach. Call out non-obvious choices. -->

## How to Test

```bash
# 1. Setup
flask db upgrade
python run.py

# 2. Steps to verify
# e.g. Visit /dashboard → filter by status → confirm results are deterministic

# 3. API check (if applicable)
curl -c /tmp/jar -b /tmp/jar http://127.0.0.1:5000/api/v1/orders?page=1&per_page=5
```

## Checklist

- [ ] Acceptance criteria from the issue are met
- [ ] No regressions: existing routes and API endpoints still work
- [ ] Demo mode still functional (auto-login, read-only guard)
- [ ] New behavior covered by a smoke test or manual test documented above
- [ ] Docs updated if any API, architecture, or decision changed
- [ ] `requirements.txt` updated if new dependencies added
- [ ] No secrets or real credentials committed

## Demo Artifact

<!-- Attach a screenshot or Loom link showing the change working -->
