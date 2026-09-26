# Architecture Decisions

Permanent decisions. `docs/MEMORY.md` holds the current state.

## ADR-001: Python and Flask, not Next.js

Decision: Build the backend in Python with Flask and SQLite.
Reason: The core work is media processing (FFmpeg), API calls and an agent backend. Python fits those best and matches the owner's existing agent stack. The guide's Next.js/Supabase/Vercel example targets a different kind of app.
Status: Accepted (proposed by the assistant; owner may override).

## ADR-002: Official Instagram Graph API only

Decision: Publish only through Meta's official Graph API on an Instagram Business or Creator account.
Reason: Unofficial libraries and browser scraping risk account restriction and break often.
Status: Accepted.

## ADR-003: Human approval before every publish

Decision: No post is published without a recorded approval of the exact media and caption. There is no bypass in v1.
Reason: Publishing is public and hard to undo; the owner wants the agent to act only with permission.
Status: Accepted.

## ADR-004: Swishy is an import source, not an automated dependency

Decision: Use Swishy for creative motion pieces; the owner exports MP4/MOV/GIF and drops the file in the inbox. No browser automation of Swishy in v1.
Reason: No public API was found. Driving a logged-in browser session is brittle and may conflict with its terms.
Status: Accepted. Revisit if Swishy publishes an API.

## ADR-005: FFmpeg-first rendering

Decision: Use FFmpeg (and MoviePy where convenient) for editing, normalizing and simple rendered videos. Remotion is optional for richer animated graphics.
Reason: Free, scriptable, no vendor lock-in.
Status: Accepted.

## ADR-006: Public media hosting for Instagram to fetch

Decision: Pending.
Options: (a) serve from this app through a tunnel only during publish; (b) free object storage with random keys and automatic deletion.
Constraint: whichever is chosen must use unguessable URLs that expire, and must clean up after publishing.
Status: Open. Decide before TASK-025.

## ADR-007: Single owner in v1, multi-user-ready data model

Decision: One login now, but every table carries `owner_id` and every query filters on it.
Reason: Cheap to do now, expensive to retrofit.
Status: Accepted.
