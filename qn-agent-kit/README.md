# QN Agent Starter Kit

A reusable project kit so you never have to re-explain an idea to an AI coding agent from scratch.

## How to use this, every time you start a new build

**Step 1 — Fill in the docs (5–10 minutes)**
Open `docs/PRD.md` and describe the idea in your own words (or paste a passage/spec — no need to reformat it, just drop it in).
Open `docs/INTEGRATIONS.md` and list every platform, API, app, or open-source tool the project should use — paste the URLs. As few as 5, as many as 60+.
Everything else in `docs/` can stay as templates — QN will fill gaps in as it works, but the more you fill in yourself, the fewer questions it asks.

**Step 2 — Open this folder in VS Code with Claude Code (or Cursor).**

**Step 3 — Paste the contents of `BOOTSTRAP_PROMPT.txt`** as your first message to Claude Code / Cursor. That's the one prompt that gets it to read everything and report back before touching code.

**Step 4 — Review its plan, answer anything it genuinely can't infer, then say "go."**
From there it works task-by-task through `TASKS.md`, updating `MEMORY.md` and `DECISIONS.md` as it goes, following `RULES.md` and `SECURITY.md` at every step.

**Step 5 — When it's done**, the project is a normal, runnable codebase — open it locally, push it to GitHub, or deploy per `ARCHITECTURE.md`. No special export step needed; it's just a folder.

## Reusing this kit
Copy this whole folder for every new project/agent you build. Rename it, wipe the `docs/` content back to templates, and start again at Step 1.
