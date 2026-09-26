# Product Requirements Document

## Product
QN

## Problem
Every time Snehasis starts a new project, he has to re-explain the idea, rules, and constraints from
scratch to whatever AI coding tool he's using. There's no consistent memory, no shared rulebook, and
no single place tracking which platforms/APIs/repos a project depends on — and switching between
tools (Claude Code, GitHub Copilot, Antigravity, Cursor) means starting over each time.

## Target Users
Snehasis Sahoo (Founder, SYB) — used across all his ventures: ORBIT AIOS, MANTRA, GRAVEN OS, Nandi,
Loan Ledger, Krishna, Scanline, Adapt Planner, Forge Your Frame, and any future project.

## Goal
A portable, reusable "brain" — docs, prompts, and protocols — that any AI coding tool can read to
understand a project's goals, architecture, rules, and integrations instantly, and then build it out
consistently, without fake/placeholder code and without re-explaining context every session.

## Core Features
1. A reusable doc scaffold (PRD, ARCHITECTURE, DESIGN, RULES, TASKS, DECISIONS, MEMORY, SECURITY,
   TEST_PLAN) — copied fresh into any new project folder.
2. A fixed prompt sequence (Bootstrap → Build → Fix/Activate) that any coding tool follows to go from
   "reads the docs" to "verified, error-free, running code."
3. A protocol for researching and integrating GitHub repos (`GITHUB_PROTOCOL.md`) — propose before
   merge, license-check, never fake an integration.
4. A single source of truth for every platform/API/tool a project uses (`INTEGRATIONS.md`) — tool-
   agnostic, never duplicated into app-specific files.
5. File-based long-term memory (`MEMORY.md` + `memory/log/`) so context survives across sessions and
   across whichever tool is being used that day.
6. Tool-agnostic by design — works with Claude Code, GitHub Copilot, Antigravity, Cursor, or any
   agent that can read local markdown files.

## MVP (what exists now, v1)
- The full doc scaffold and the three prompts (bootstrap, build, fix-and-activate)
- `GITHUB_PROTOCOL.md` and `MEMORY_SYSTEM.md`
- A populated `INTEGRATIONS.md` workflow, with categorization (programmatic / self-hosted /
  reference-only / needs-a-decision)
- A minimal, real status tool (per `BUILD_QN_PROMPT.txt`) that reports project state from the docs

## Out of Scope (not v1 — future ideas, not commitments)
- A standalone app or dashboard UI for QN itself
- Autonomous background operation outside of scheduled Routines
- Voice interface
- Automatic account management (e.g. a dedicated Gmail login/logout cycle)
- Merging with unrelated pre-existing apps (like the site-builder app already in some workspaces) —
  those stay separate projects unless explicitly folded in

## Success Criteria
Snehasis should be able to:
1. Drop this kit into any new or existing project folder
2. Run the 3-prompt sequence with whichever coding tool he's using that day
3. Have the agent understand the project's goals, rules, and integrations without being re-explained
4. Get real, verified, working code back — no placeholder functions, no fake "done" reports
5. Come back days later (new session, possibly a different tool) and have it pick up exactly where it
   left off, via `MEMORY.md` and `memory/log/`
