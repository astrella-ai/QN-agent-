# Architecture

## Relationship to docs/FOUNDER_OS_VISION.md
That file is the complete target system. This file is how we actually get there without producing
fake/stubbed components — build the smallest real spine first, verify it end-to-end, then expand one
subsystem at a time. Every subsystem below maps to something named in the vision doc; nothing is
invented here that isn't in it, and nothing in it is skipped — just sequenced.

## The Spine (build and verify this before anything else)
The minimum system that proves the whole architecture actually works, end-to-end, for real:

1. **Orchestrator** — receives a founder request, breaks it into a Task Graph, decides which agent
   handles each piece
2. **Permission Engine** — capability-based permissions (ALLOWED / DENIED / ASK_EVERY_TIME / ASK_ONCE
   / PROJECT_ONLY / SESSION_ONLY), enforced before any sensitive action
3. **Task Graph + Task Management Engine** — persistent tasks with real states (QUEUED, PLANNING,
   EXECUTING, VERIFYING, BLOCKED, COMPLETED, etc.)
4. **Tool Registry + Capability Registry** — even if nearly empty at first, these must be real and
   queried before any capability is assumed to exist
5. **One working agent** (Research Agent is the right first choice — lowest risk, easiest to verify)
   wired through the full loop: UNDERSTAND → PLAN → EXECUTE → VERIFY → REGISTER → REPORT
6. **Verification Agent** — independently checks the Research Agent's output before it's reported as
   done — this is what proves the "no fake autonomy" rule actually holds structurally, not just by
   good intentions

Nothing else gets built until this spine is VERIFIED (per docs/RULES.md's status vocabulary) working
end-to-end on a real, simple task.

## Full Target Architecture (from the vision doc, for reference)
```
Founder UI ↔ API ↔ Orchestrator ↔ Persistent Queue ↔ Workers ↔ Agents ↔ Tools ↔ Verification ↔ Database
```
Agents: Orchestrator, Research, Browser, Coding, File, System, Media, Data, Testing, Security, Memory,
Monitoring, Planning, Verification (+ dynamically addable specialized agents)

Registries: Tool Registry, Software Inventory, Capability Registry, Project Registry

Execution split:
```
Browser/UI → Orchestrator → Permission Engine → Local Bridge → Local Tool → Verification → Result
```
Browser/remote execution is the default; the Local PC Bridge activates only for tasks that genuinely
need local resources (GPU, local files, Windows apps, terminal/PowerShell), and only after explicit
permission for that specific operation.

## Phased Build Order (after the Spine is verified)
- **Phase A (Spine):** Orchestrator, Permission Engine, Task Graph, Tool/Capability Registry, Research
  Agent, Verification Agent — see above
- **Phase B:** Browser Automation Agent (navigation, DOM extraction, clicking, screenshots) + GitHub
  Agent (read-only first)
- **Phase C:** Local PC Bridge (file/terminal/PowerShell, permission-gated) + File Agent + System Agent
- **Phase D:** Coding Agent + Code Execution Sandbox + Testing Agent
- **Phase E:** Memory architecture (short-term / project / preferences / technical / execution / audit
  — separate stores, not one blob) + Knowledge Ingestion Engine
- **Phase F:** 24/7 Agent Runtime — persistent queues, background workers, scheduler, heartbeat, crash
  recovery — this is what makes the system survive browser disconnection
- **Phase G:** Voice Agent (STT → intent → planning → execution → TTS, with interruption/resume) +
  multilingual support, using docs/PERSONA.md for tone
- **Phase H:** Media Agent, Security Agent, Resource Manager, Model Router, remaining specialized
  agents as needed
- **Phase I:** Founder Dashboard — real-time task graph, activity log, approval requests, agent
  health, all driven by actual backend state (per FOUNDER_OS_VISION.md — never decorative)
- **Phase J:** `/diagnose` and `/audit` commands, synchronization engine (DB ↔ filesystem ↔ process ↔
  installed software state), full audit logging

## Non-negotiable rules carried from the vision doc
- The database/runtime is the source of truth for execution state — never the LLM's claim alone.
- No UI element connects to anything that isn't real backend logic.
- No capability is marked ACTIVE until the Verification Agent (or equivalent test) confirms it.
- The Local PC Bridge never gets unrestricted OS control from the browser/UI layer directly.
- Every sensitive action (delete, install, spend, publish, account access) goes through the
  Permission Engine — no exceptions, no "trusted mode" that skips it.

## Folder Structure (Phase A/B scope — expands per phase)
```
orchestrator/
├── src/
│   ├── task-graph/
│   ├── permission-engine/
│   ├── registries/        (tool, capability, project)
│   ├── agents/
│   │   ├── research/
│   │   └── verification/
│   ├── api/
│   └── db/
```
