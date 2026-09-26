# Product Requirements Document

## Product
QN — Personal AI Agent (hybrid local + cloud)

## Problem
Snehasis wants one continuously-available assistant — reachable by voice or text, aware of what was
left unfinished, able to act on his PC, able to code and build things itself, and able to learn from
a link or video he hands it — rather than a narrow single-purpose tool.

## Target User
Snehasis Sahoo — personal use, across all SYB ventures.

## Goal
A hybrid agent: a small always-on cloud presence keeps it reachable 24/7 for conversation, memory,
and research even when the PC is off; a local companion app handles anything PC-specific (files,
apps, screen, VS Code) when the PC is on and connected.

## Full Vision (the complete feature set — built in phases, see Roadmap below)
1. Wake-word activated, continuous voice conversation loop — say its name, it's listening; keeps
   talking until told to stop
2. Multilingual conversation — Hindi, English, and others, switching naturally
3. Invisible session continuity — picks up naturally ("want to continue what we started yesterday?")
   without ever narrating that it checked memory
4. A tiered permission system for actions (see Security below) instead of either "confirm everything"
   or "confirm nothing"
5. Cloud presence for 24/7 reachability; local agent for PC-specific + screen-level work
6. Learn-from-link — hand it a YouTube URL or article, it extracts what's being taught/asked and
   either does it, asks for a missing resource, or proposes a plan
7. Self-coding — can open and drive VS Code, write real code, following the QN kit's own RULES.md and
   SECURITY.md so it never fakes completion
8. Dashboard structure — separate sections per venture/category, auto-filing new work under the
   right one
9. Platform ingestion — paste a URL and say "add this," it logs it in INTEGRATIONS.md and wires it in
   per GITHUB_PROTOCOL.md — asks for credentials/payment when needed, never bypasses a paywall or
   license gate on its own

## MVP (build and ship this first — everything else is Phase 2+)
- Local app, text + voice, one continuous session per launch
- Basic wake-word activation and a natural "pick up where we left off" opener
- Tier 1 + Tier 2 actions only (read/search/write-with-light-confirm) — no screen control, no
  autonomous coding yet
- Local memory (as already scoped) — cloud sync comes in Phase 2

## Roadmap (explicitly not in MVP — sequenced, not simultaneous)
- **Phase 2:** Cloud presence backbone — persistent session/memory sync, reachable by text even when
  the PC is off
- **Phase 3:** Full tiered permission system + screen-level PC control (Tier 3 actions, always
  confirmed)
- **Phase 4:** Learn-from-link (YouTube/article ingestion)
- **Phase 5:** Self-coding / VS Code control
- **Phase 6:** Dashboard UI, per-venture sections
- **Phase 7:** Platform ingestion via chat ("download and connect this")

## Out of Scope (not committed, even long-term, unless revisited)
- Bypassing paywalls, license gates, or payment requirements — it asks, it never works around them
- Any action in Tier 3 (delete, purchase, install system-level software, act on another account)
  ever running without explicit confirmation, at any phase

## Success Criteria (MVP)
1. Say its name or type to it — it responds, in the language used, picking up context naturally
2. It can search, read files, and write new files with a lightweight confirmation
3. Closing and reopening it retains the conversation
4. It never performs a destructive or costly action without asking first
