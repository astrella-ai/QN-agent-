# Architecture

## What QN actually is
QN is not a single application with one fixed tech stack. It's a portable set of markdown docs and
plain-text prompts that gets copied into any project folder — new or existing — and read by whatever
AI coding tool is being used that day. The "architecture" that matters is the structure of the kit
itself, not a frontend/backend/database triad.

## The kit's own structure
```
qn-agent-kit/
├── AGENT_INSTRUCTIONS.md      ← read first, every time
├── BOOTSTRAP_PROMPT.txt       ← step 1: understand the project, report back
├── BUILD_QN_PROMPT.txt        ← step 2: construct a verified, error-free skeleton
├── FIX_AND_ACTIVATE_PROMPT.txt← step 3: fix errors, categorize + wire integrations, verify live
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   ├── PRD.md                 ← what this specific project is (fill in per-project)
│   ├── ARCHITECTURE.md        ← how this specific project is built (fill in per-project)
│   ├── DESIGN.md
│   ├── RULES.md
│   ├── INTEGRATIONS.md        ← single source of truth for every URL/API/repo this project uses
│   ├── GITHUB_PROTOCOL.md
│   ├── MEMORY_SYSTEM.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   ├── MEMORY.md
│   ├── SECURITY.md
│   └── TEST_PLAN.md
└── memory/
    └── log/                   ← dated session history, append-only
```

## When QN is applied to an actual project
The project being built (whatever it is) chooses its own real stack in ITS OWN `docs/ARCHITECTURE.md`
— e.g. Next.js + Supabase for a web app, or nothing at all if the "project" is just research. QN's
job is to make sure whichever stack gets picked is documented, followed consistently, and never
silently changed without an entry in `DECISIONS.md`.

## The one piece of QN that is real running code
Per `BUILD_QN_PROMPT.txt` step 3, each project gets a small status script (language matches the
project's own stack — Node if it's a JS project, Python if it's a Python project, etc.) that reads
`docs/INTEGRATIONS.md`, `docs/TASKS.md`, and `docs/MEMORY.md` and reports real project state. This
is intentionally minimal — a sanity-check tool, not a dashboard product.

## Rules
- QN's own docs (this folder) never get replaced by a project's actual source code — they sit
  alongside `src/`, not inside it.
- A project's real architecture decisions go in that project's own `docs/ARCHITECTURE.md` and
  `docs/DECISIONS.md`, not here.
- If QN is dropped into a folder that already has unrelated app code, flag that per
  `AGENT_INSTRUCTIONS.md`'s portability rule — don't silently merge into it.
