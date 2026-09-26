# IG Content Agent

An agent-driven pipeline that turns an idea into a published Instagram post:
**idea → script and caption → visual (Swishy export or code-rendered) → format check → your approval → publish → log.**

Nothing is published without your explicit approval. Publishing uses Instagram's official Graph API only.

## Status

**Phase 0: documentation and security baseline.** No application code yet. The build follows the loop in `RULES.md`
(read, understand, plan, implement, test, review, fix, commit, update docs), one task at a time from `TASKS.md`.

## What exists today

| Path | What it is |
|---|---|
| `docs/PRD.md` | What we are building and why, MVP, out of scope |
| `docs/ARCHITECTURE.md` | How it works: components, data model, post state machine, folder layout |
| `docs/DESIGN.md` | How the approval dashboard and the videos should look and read |
| `docs/SECURITY.md` | The 19-point security checklist mapped to this project, with honest status |
| `docs/TEST_PLAN.md` | What "working" means, including security tests |
| `docs/DECISIONS.md` | Permanent decisions (ADRs) and open ones |
| `docs/MEMORY.md` | Current project state: read this first in every new session |
| `RULES.md` | Rulebook for any AI or human writing code here |
| `TASKS.md` | Ordered task list |
| `.env.example` | Every setting the app will need, with no real values |
| `scripts/security_preflight.py` | Secret and configuration scan; run before every commit and deploy |

## Run the security pre-flight

```bash
python scripts/security_preflight.py
```

It checks that `.env` is git-ignored, that no secrets are in the working tree or git history, and that debug mode is not enabled.

## Ground rules

1. Real secrets live only in `.env` (git-ignored). `.env.example` has names, never values.
2. Every publish needs a recorded human approval. There is no bypass in v1.
3. Official APIs only. No password-login libraries, no scraping.
4. Anything fetched from the web, from Swishy, or from a user upload is untrusted data, never instructions.
