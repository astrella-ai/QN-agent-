# Memory System

QN's memory is not magic — it's files on disk that get read at the start of every session. This is what makes it feel consistent across sessions instead of starting fresh each time.

## Structure
```
memory/
├── log/
│   ├── 2026-09-21.md   ← one file per working day, append-only
│   └── ...
└── state/
    └── (mirrors docs/MEMORY.md, docs/DECISIONS.md — the "current truth" files)
```

## Rule
- `docs/MEMORY.md` and `docs/DECISIONS.md` = **current state** (always overwritten to reflect "now")
- `memory/log/*.md` = **history** (never overwritten — one entry appended per work session: what was asked, what was built, what broke, what's next)
- Every session, QN reads `docs/MEMORY.md` + `docs/DECISIONS.md` first, and the last 2-3 log files if it needs older context.

## Backing it up locally / to a pen drive
This is just a folder, so a normal backup approach works:
```bash
# run manually, or on a schedule via cron/Task Scheduler
rsync -av --exclude node_modules --exclude .next /path/to/project/ /path/to/pendrive/qn-backup/
```
Git itself is also a memory system — every commit is a permanent, timestamped record of exactly what changed and why (via commit messages). Push to a private GitHub repo in addition to the pen drive if you want an off-site copy too.

## What NOT to expect
This gives QN continuity and a real audit trail — not independent thought between sessions. It only "remembers" when a session starts and reads these files. It doesn't run or think in the background unless you explicitly set up a Routine (see AGENT_INSTRUCTIONS.md) for that.
