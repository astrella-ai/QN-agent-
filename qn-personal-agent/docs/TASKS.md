# Tasks

## Phase 1: MVP — Local text + voice, one session
- [ ] Initialize Electron + React + TypeScript project (local-app/)
- [ ] Configure local SQLite for session memory
- [ ] Wire chat to Gemini (via a thin local service call for now — cloud proxy comes in Phase 2)
- [ ] Build chat UI
- [ ] Add basic wake-word detection + mic input
- [ ] Add Coqui TTS voice output
- [ ] Build the Tier 1/Tier 2 action framework (search, read file, write file with light confirm)
- [ ] Verify: open app, talk or type, get a response, close and reopen, conversation is retained

## Phase 2: Cloud presence backbone
- [ ] Stand up cloud-service/ (API + DB)
- [ ] Move conversation/memory source-of-truth to cloud DB
- [ ] Local app syncs with cloud on connect, caches for offline use
- [ ] Add a lightweight text-reachable surface (web chat) for when the PC is off
- [ ] Verify: message it while the PC/local app is off, get a response; reconnect PC, state is consistent

## Phase 3: Full tiered permissions + screen control
- [ ] Formalize Tier 3 action list and confirmation flow
- [ ] Add screen-level PC control actions (behind Tier 3 confirmation, always)
- [ ] Verify: attempt a Tier 3 action, confirm it never executes without explicit approval

## Phase 4: Learn-from-link
- [ ] Add YouTube URL ingestion (transcript/summary extraction)
- [ ] Add general article/doc URL ingestion
- [ ] Verify: give it a tutorial link, it correctly identifies what's being taught and proposes next steps

## Phase 5: Self-coding / VS Code control
- [ ] Add VS Code control capability to the local app
- [ ] Wire in the existing qn-agent-kit RULES.md/SECURITY.md so self-coding follows the same discipline
- [ ] Verify: give it a small coding task, it opens VS Code, writes real code, runs tests, reports honestly

## Phase 6: Dashboard
- [ ] Design per-venture sections (Website, ORBIT, Loan Ledger, etc.)
- [ ] Auto-file new work under the correct section
- [ ] Verify: create work in two different categories, confirm each lands on its own page

## Phase 7: Platform ingestion via chat
- [ ] Add "paste a URL, say add this" flow
- [ ] Auto-log to docs/INTEGRATIONS.md, follow docs/GITHUB_PROTOCOL.md for repos
- [ ] Verify: paste a new platform URL, confirm it's logged and categorized correctly, nothing wired
      in silently without a report back
