# Architecture Decisions

Permanent decisions. `docs/MEMORY.md` holds the current state.

## ADR-001: Python and Flask, with almost no dependencies
Decision: Flask, waitress and Pillow only. SQLite from the standard library. AI providers and Instagram over plain HTTPS.
Reason: media work fits Python; fewer dependencies means easier install on a PC and fewer things to update or attack.
Status: Accepted.

## ADR-002: Official Instagram Graph API only
Decision: publish only through Meta's API on a Business or Creator account.
Reason: unofficial tools risk account restriction and break often.
Status: Accepted.

## ADR-003: Human approval before every publish
Decision: no post is published without a recorded approval of the exact media and caption, re-verified at publish time. There is no bypass, including by voice or by the automation agent.
Reason: publishing is public and hard to undo.
Status: Accepted.

## ADR-004: Swishy is an import source
Decision: use Swishy in the browser and drop the export into the inbox folder. No browser automation of Swishy.
Reason: no public API found; automating a logged-in session is fragile and may breach its terms. Revisit if it publishes an API.
Status: Accepted.

## ADR-005: FFmpeg-first rendering
Decision: FFmpeg for conversion; Pillow to draw text frames piped into FFmpeg.
Reason: free, scriptable, no vendor lock-in, no font path problems on Windows.
Status: Accepted.

## ADR-006: Public media through a separate server
Decision: a second server on its own port serves only `/m/<token>/<file>` links that expire; the owner's tunnel points at that port.
Reason: Instagram must download the video, but the dashboard must never be on the internet.
Status: Accepted (replaces the earlier open question).

## ADR-007: One owner, multi-user-ready data
Decision: one sign-in now; every table has `owner_id` and every query filters on it.
Status: Accepted.

## ADR-008: Voice in the browser, plus optional speech on the PC
Decision: listening and speaking use the browser's speech features so it works on PC and phone without installing anything. The PC's own speech tool is used only for alerts and the start-up briefing.
Reason: browsers cannot speak before a first touch, so an app that starts by itself needs a PC-side voice for the start-up greeting.
Status: Accepted.

## ADR-009: Server-sent events for the live screen
Decision: one SSE stream instead of WebSockets.
Reason: no extra software, passes through Tailscale and tunnels, reconnects by itself and replays missed events.
Status: Accepted.

## ADR-010: The assistant proposes; the owner taps
Decision: voice and chat can start drafts and edit, but approve, publish and reject create a confirmation card bound to the exact content.
Reason: speech recognition mistakes and prompt injection must never cause a public post.
Status: Accepted.

## ADR-011: Start at sign-in, not as a system service
Decision: a scheduled task at sign-in (launchd or systemd user unit elsewhere).
Reason: the app needs the owner's desktop session (browser, PC speech) and needs no administrator rights.
Status: Accepted.

## ADR-012: Dry run is the default
Decision: `DRY_RUN=1` until the owner changes it.
Reason: the first thing anyone does with a publishing tool must not be a public post.
Status: Accepted.
