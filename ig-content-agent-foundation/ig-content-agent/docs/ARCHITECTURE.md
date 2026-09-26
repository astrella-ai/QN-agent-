# Architecture

Architecture = HOW.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Best fit for FFmpeg/MoviePy, API clients and an agent backend |
| Web | Flask | Small, matches the owner's existing agent stack |
| Database | SQLite (via SQLAlchemy) | Zero setup, single user; swap to PostgreSQL later without code changes |
| Video | FFmpeg / ffprobe (MoviePy optional) | Free, scriptable, reliable |
| Visual editors | Swishy (manual export, imported), optional Remotion | See ADR-004 |
| Publishing | Instagram Graph API | Official; see ADR-002 |
| Auth | Session login, argon2 or bcrypt password hash | See `docs/SECURITY.md` |
| Testing | pytest, Playwright for E2E | |

The guide's example stack (Next.js, Supabase, Vercel) is for a different kind of product. This one is a media pipeline with an approval UI, so Python is the better fit (ADR-001).

## Data flow

```
Owner (browser)
   |
   v
Flask routes (thin)  --auth, CSRF, validation-->  Services (business logic)
                                                     |
        +--------------------+-----------------------+---------------------+
        v                    v                       v                     v
  LLM provider         Renderers               Approval + state       Publisher
  (captions,           (ffmpeg, template,      machine + activity     (Instagram
   scripts)             Swishy import)         log (SQLite)            Graph API)
                             |                                            ^
                             v                                            |
                        Media storage  ---- public URL (short-lived) -----+
                        (instance/media)
```

## Post state machine

```
DRAFT -> RENDERING -> READY_FOR_REVIEW -> APPROVED -> PUBLISHING -> PUBLISHED
                             |                |            |
                             v                v            v
                         REJECTED        (edit resets    FAILED (retry allowed)
                                          to READY_FOR_REVIEW)
```

Rules:
- Only `APPROVED` posts can enter `PUBLISHING`. The publisher re-checks this itself, not just the route.
- Editing the caption or media after approval resets the post to `READY_FOR_REVIEW` and clears the approval.
- The approval record stores a hash of the exact media file and caption that were approved. The publisher refuses to send anything that does not match.

## Data model (first version)

- `users`: id, username, password_hash, created_at
- `posts`: id, owner_id, brief, caption, hashtags, media_type (REEL / IMAGE / CAROUSEL / STORY), state, created_at, updated_at
- `assets`: id, owner_id, post_id, kind, storage_key (random), sha256, duration, width, height, size_bytes, source (upload / swishy_inbox / rendered)
- `approvals`: id, owner_id, post_id, media_sha256, caption_sha256, approved_at
- `publish_attempts`: id, owner_id, post_id, container_id, status, error_code, created_at
- `activity_log`: id, owner_id, post_id, level, message, permission_level, created_at

Every table with user data has `owner_id`, and every query filters on it.

## Permission levels

| Level | Examples here |
|---|---|
| Observe | Read posts, list assets, check the publishing limit |
| Create | Generate a caption, render a new video file |
| Modify | Edit a draft, replace an asset |
| External Action | Publish to Instagram, call a paid API |
| Critical | Rotate or delete tokens, delete a published post |

Approval prompts are grouped per post, not per tiny step: one approval covers "render, then publish this exact video and caption".

## Instagram publishing flow

1. Confirm state is `APPROVED` and hashes match.
2. Check the account's publishing limit endpoint.
3. Make the media reachable at a short-lived, unguessable public URL (Instagram fetches it).
4. Create a media container (type Reel / image / story / carousel children, plus caption).
5. Poll the container until it reports finished; handle errors and timeouts.
6. Call publish; store the returned media id and permalink.
7. Remove the public URL and the temporary copy.

`DRY_RUN=1` runs steps 1 to 3 and stops before step 4.

## Folder structure

```
ig-content-agent/
  app/
    __init__.py            app factory
    config.py              settings from env, fails closed
    routes/                auth, dashboard, posts, api (thin)
    services/              posts, assets, approvals, activity
    security/              auth, csrf, headers, limits, uploads, redaction
    providers/llm/         one adapter per LLM provider
    renderers/             ffmpeg_renderer, template_renderer, swishy_import
    publishers/            instagram.py
    models/
    templates/  static/
  tests/  unit/ integration/ e2e/
  scripts/                 security_preflight.py
  instance/                gitignored: database, media, inbox
  docs/
```

## Architectural rules

- Routes only parse input, call a service, and return a response.
- Services hold business logic. Only services and models touch the database.
- Renderers and publishers sit behind small interfaces so tools can be swapped (Swishy, Remotion, other APIs).
- All subprocess calls go through one helper that takes an argument list.
- Configuration is read once in `config.py`. No other module reads environment variables.
- External text (web pages, uploads, LLM output) is treated as data and validated before use.

## Integration with the owner's automation agent

The app exposes a small authenticated API so the agent can call it as a tool. Each endpoint is tagged with a permission level, and the agent needs a recorded approval before any External Action. The agent can propose 2 to 3 tool options for a step, wait for a choice, execute, and get a notification on completion, matching the agent's existing propose-then-approve flow.
