# Tasks

Work one task at a time: understand, plan, implement, test, review, commit, update docs.
`[you]` = needs the owner. `[agent]` = the assistant or automation agent can do it.

## Phase 0: Pre-flight (docs and security baseline)

- [x] Write PRD, ARCHITECTURE, DESIGN, SECURITY, TEST_PLAN, DECISIONS, MEMORY, RULES, README
- [x] `.gitignore`, `.env.example`
- [x] `scripts/security_preflight.py`
- [ ] TASK-001 [agent+you] `git init`, create a PRIVATE GitHub repo, first commit (docs only)
- [ ] TASK-002 [agent] Run the pre-flight; add it as a pre-commit hook and a CI check
- [ ] TASK-003 [agent] Python venv, pinned dependencies, verify `ffmpeg` and `ffprobe` are installed
- [ ] TASK-004 [you] Make the Instagram account Business or Creator; link it to a Facebook Page (complete Page Publishing Authorization if asked)
- [ ] TASK-005 [you] Create a Meta developer app; add your own account with a role on the app

## Phase 1: Foundation and security baseline

- [ ] TASK-006 App factory and config loader (environment only; refuse to start if `SECRET_KEY` is missing)
- [ ] TASK-007 Production-safe defaults: debug off, generic error pages, redacted server logs
- [ ] TASK-008 Security headers and locked CORS allowlist
- [ ] TASK-009 Database, migrations, `users` table, `owner_id` on all data tables
- [ ] TASK-010 Login (hashed password), secure session cookies, CSRF, login rate limit
- [ ] TASK-011 Route protection: login required everywhere, admin decorator, owner-check helper
- [ ] TASK-012 Tests for Phase 1 (logged-out access, headers, debug off, rate limit, cross-user access)

## Phase 2: Assets and rendering

- [ ] TASK-013 Upload endpoint with full validation, random filenames, storage outside web root
- [ ] TASK-014 Swishy inbox: import exported MP4/MOV/GIF from the inbox folder
- [ ] TASK-015 `ffprobe` validator with clear pass/fail reasons
- [ ] TASK-016 FFmpeg normalizer to 1080x1920 H.264/AAC MP4 (argument lists only)
- [ ] TASK-017 Template renderer: text and images to video with burned-in captions

## Phase 3: Content generation

- [ ] TASK-018 LLM provider abstraction (key from environment; swappable)
- [ ] TASK-019 Caption, hashtag and script generator (external text treated as data)
- [ ] TASK-020 Brief intake form with server-side validation

## Phase 4: Approval flow

- [ ] TASK-021 Post state machine and activity log
- [ ] TASK-022 Approval inbox UI: phone preview, caption editor, checks, actions (see DESIGN.md)
- [ ] TASK-023 Approve / send back / reject endpoints with owner and state checks; approval hash

## Phase 5: Instagram publishing

- [ ] TASK-024 Token storage, refresh and redaction
- [ ] TASK-025 [you decide, agent builds] Public media hosting per ADR-006, with expiring URLs and cleanup
- [ ] TASK-026 Publisher: create container, poll status, publish; DRY_RUN on by default
- [ ] TASK-027 Publishing limit check, retry with backoff, failure states
- [ ] TASK-028 [you] First live test post to your account (approval required)

## Phase 6: Agent integration and logging

- [ ] TASK-029 Authenticated tool interface for the automation agent, each endpoint tagged with a permission level
- [ ] TASK-030 Result log (Google Sheet: name, link, summary) and completion notifications

## Phase 7: Hardening and release

- [ ] TASK-031 Full review against `docs/SECURITY.md`
- [ ] TASK-032 Code review and QA on a preview environment
- [ ] TASK-033 Production deploy: environment variables, monitoring, backups
- [ ] TASK-034 Rotate all tokens; confirm nothing sensitive is in git history
