# Architecture (v2)

Architecture = HOW.

## Overview

One Python process on the owner's PC. It serves the dashboard, runs background workers, and runs a second tiny server that only hands Instagram short-lived media links.

```
 Phone / PC browser (installable web app)
   |  https (Tailscale) or http://localhost
   v
+-------------------------------- one process: python manage.py run ------------------------------+
|  Web server (waitress)  port 5057                                                                |
|    Flask app: pages, JSON API, live event stream (SSE), agent API                                |
|      security layer: host check, CSRF, sessions, rate limits, headers                            |
|      services: posts + state machine + approvals, job queue, assistant                           |
|                                                                                                  |
|  Background threads                                                                              |
|    media worker   generate_content, normalize, render_template                                  |
|    publish worker publish (Instagram)                                                           |
|    watcher        inbox folder, scheduler, cleanup, heartbeats                                   |
|                                                                                                  |
|  Public media server  port 5058  -> serves only /m/<token>/<file>, links expire                  |
|                                                                                                  |
|  SQLite (instance/app.db)   instance/media   instance/inbox   instance/logs                      |
+--------------------------------------------------------------------------------------------------+
   |                 |                    |                       ^
   v                 v                    v                       | tunnel to port 5058 only
 FFmpeg          AI provider          Instagram Graph API --------+ (Instagram fetches the video)
 (local)         (optional)           (official, HTTPS)
```

## Real time

The browser opens one server-sent-events stream (`/api/events`). Every activity-log entry and every post state change is pushed to it. On reconnect the browser sends the last event id and missed activity is replayed. Chosen over WebSockets because it needs no extra software, works through Tailscale and tunnels, and reconnects by itself (ADR-009).

## Post state machine

```
DRAFT -> RENDERING -> READY_FOR_REVIEW -> APPROVED -> PUBLISHING -> PUBLISHED
   ^          |              |   |            |           |
   |          |              |   +-> REJECTED |           +-> FAILED (retry allowed)
   |          v              v                v
   +---- back to DRAFT when the caption, media or type changes (approval revoked)

APPROVED -> PUBLISHING -> DRY_RUN_COMPLETE (dry-run mode; can later be published for real)
```

Rules that are enforced in code and tested:
- Only `READY_FOR_REVIEW` posts with no blocking checks can be approved.
- An approval stores the hash of the exact media files and the caption. Any change revokes it.
- The publisher re-verifies the approval and re-hashes the files on disk immediately before publishing.
- Voice and agent paths use the same functions; none can skip the gate.

## Jobs

Work is stored in the `jobs` table, so it survives a restart (`running` jobs return to `queued` at start). Two worker threads claim jobs atomically. Temporary Instagram errors retry with backoff (30 s, 60 s, then fail); other failures stop with a readable message.

## Assistant

`POST /api/assistant` builds a small `<state>` block (counts, recent posts, recent activity), sends it with the owner's message to the AI provider, and expects `{"speech", "action"}`. Without a provider a local command parser is used. Actions are a fixed whitelist. `approve_post`, `approve_and_publish` and `reject_post` only create a pending confirmation (5 minutes, single use, bound to the media and caption hashes, bound to the owner). Text inside `<state>` is labelled as data.

## Voice

Listening and speaking use the browser's built-in speech features (no audio is stored by the app). The PC can also speak through its own speech tool for alerts and a start-up briefing; text is passed on standard input, never on the command line.

## Starting by itself

`manage.py install-autostart` registers a Windows scheduled task at sign-in (launchd on macOS, a systemd user unit on Linux). The app opens no window (pythonw), writes `instance/logs/app.log`, and refuses to start a second copy (the port is taken).

## Data model

`users`, `posts`, `assets` (storage_key = original, ready_key = converted), `approvals`, `publish_attempts`, `jobs`, `activity`, `messages`, `pending_actions`, `public_links`, `kv`. Every user-data table carries `owner_id` and every query filters on it.

## Permission levels

| Level | Examples |
|---|---|
| Observe | List posts, status, briefing |
| Create | Make a draft, write a caption, render a video, add media |
| Modify | Edit a caption, schedule, approve, reject, send back |
| External Action | Publish to Instagram |
| Critical | (reserved) rotating tokens, deleting published posts: not automated |

Each activity-log entry records its level, so the feed shows what kind of action happened.

## Folder structure

```
manage.py                 setup, doctor, run, autostart, password, agent token
app/
  __init__.py             app factory, context wiring, log redaction
  config.py               settings from .env, fails closed
  db.py                   SQLite, schema
  security.py             host check, CSRF, sessions, rate limits, headers
  services.py             posts, approvals, state machine, job queue
  pipeline.py             uploads, conversion, job runner, workers, inbox, scheduler
  media.py                content sniffing, ffprobe, FFmpeg, text-to-video
  publisher.py            approval re-check, dry run, live publishing
  instagram.py            Graph API client
  publicmedia.py          separate media-link server
  assistant.py            conversation, actions, confirmations
  llm.py                  AI providers over HTTPS + offline fallback
  notify.py               PC speech, Telegram
  events.py               live event bus, activity log
  routes/                 auth, pages, api, agent
  templates/  static/     login and app shell, JS, CSS, service worker, icons
tests/                    73 automated tests
scripts/security_preflight.py
docs/
```

## Architectural rules

- Routes parse input and call services. Only services and pipeline code touch the database.
- Configuration is read once in `config.py`.
- Subprocesses take argument lists; file names on disk are generated, never from the client.
- External text (files, the web, AI output) is data and is validated before it is used.
- No inline scripts or styles, no HTML injection: all page text is set with `textContent`.
