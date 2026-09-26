# Test Plan

Defines what "working" means. Each item becomes an automated test where practical.

## Authentication and access

- Logged-out request to any dashboard or API route redirects to login (or returns 401)
- Wrong credentials show a generic error
- Login is rate limited after repeated failures
- Session cookie is HttpOnly, Secure (in production) and SameSite
- Requests without a valid CSRF token are rejected

## Authorization and data isolation

- User A cannot read, edit, approve or publish User B's post (403 or 404)
- Sending a different `user_id` or `owner_id` in a request has no effect
- Agent API credential cannot use dashboard-only actions

## Approval and publishing

- A post that is not `APPROVED` cannot be published by any route, service call or agent tool
- Editing caption or media after approval clears the approval
- Publisher refuses if the media or caption hash differs from the approved one
- `DRY_RUN=1` never calls the publish endpoint
- Publishing limit is checked before a publish attempt
- Failed publish leaves the post in `FAILED` with a readable reason and allows retry
- Public media URL stops working after publishing

## Assets and rendering

- Upload rejects: wrong extension, correct extension with wrong content (for example an executable renamed to .mp4), oversize files, path-traversal filenames
- `ffprobe` validator reports clear reasons (resolution, duration, codec, size)
- Normalizer outputs 1080x1920 H.264/AAC MP4
- Captions containing quotes, newlines, `$()` and emoji render correctly and cannot inject a command

## Input and output safety

- Caption containing `<script>` or HTML is stored as text and displayed escaped
- SQL metacharacters in any field do not change query behaviour
- Overlong fields are rejected with a clear message

## Configuration and headers

- App refuses to start without `SECRET_KEY`
- Debug mode is off in production; a forced server error shows a generic page with no stack trace
- Security headers are present on every response
- CORS does not return `Access-Control-Allow-Origin: *`; unknown origins are refused
- Logs contain no tokens, keys or passwords
- `python scripts/security_preflight.py` passes

## Dashboard (responsive and accessibility)

Test at 375, 768 and 1440 px.

- Loading, empty and error states visible
- Keyboard-only approval works, focus is visible
- Safe-zone overlay toggles

## Instagram integration (test account first)

- Publish a Reel, an image and a carousel to a test Business/Creator account
- Expired or revoked token produces a clear "reconnect" message and no crash
- Container timeout is handled and retried safely without double-posting

## End-to-end

Open dashboard, log in, submit brief, review generated caption, add video, pass format check, edit caption, approve, publish (DRY_RUN then live), see result in the log, refresh, log out.
