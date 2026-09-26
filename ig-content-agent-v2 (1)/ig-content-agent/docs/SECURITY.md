# Security Requirements (v2)

Status key: **Done** = built and covered by an automated test (test file in brackets). **Setup** = the app supports it, you must turn it on. **N/A** = not used, with the trigger that would make it apply.

| # | Checklist item | How it is handled | Status |
|---|---|---|---|
| 1 | Secure your API keys | Keys live only in `.env` (or real environment variables), read once in `config.py`, never sent to the browser, never in URLs (Instagram token in the request body, AI keys in headers), masked in logs, absent from activity records and error messages. | Done [test_publisher, test_misc] |
| 2 | Hide all `.env` files | `.env` and `.env.*` are git-ignored; `.env` is created with owner-only permissions; the pre-flight fails if one is tracked. | Done [preflight] |
| 3 | Never hardcode secrets | `init` generates the secret key and stores only a password hash; `.env.example` has no real values (tested); pre-flight scans the tree. | Done [test_misc, preflight] |
| 4 | Add authentication | Password sign-in (scrypt hash), HttpOnly SameSite session cookie, sign-out, 7-day session, constant-time check even for unknown users. | Done [test_security] |
| 5 | Verify permissions server-side | Every page and API route requires a session; the agent API needs its own token and cannot approve or publish; the assistant cannot approve or publish without a tap. | Done [test_security, test_assistant] |
| 6 | Don't trust frontend user IDs | The owner id comes only from the session (or the agent token). No endpoint accepts a user id. | Done [test_security] |
| 7 | Isolate user data | `owner_id` on every table and in every query, including media downloads and confirmations. Only one owner exists today. | Done [test_security, test_assistant] |
| 8 | Lock down your database | SQLite file in `instance/` (git-ignored, not served), WAL mode, parameterized queries. Back up `instance/` yourself. | Done; backups are Setup |
| 9 | Secure Firebase, Supabase, storage | Not used. Public media is a separate server serving only expiring random links; if cloud storage is added later it must be private with signed URLs. | N/A |
| 10 | Protect admin routes | There is one role. The dashboard, the API and the live stream all require sign-in; the public media server exposes nothing else (tested). | Done [test_runtime] |
| 11 | Disable production debug mode | The app refuses to start with `FLASK_DEBUG=1` in production; pre-flight flags `debug=True`. | Done [test_security] |
| 12 | Hide detailed errors | Users see a generic message; details go to `instance/logs/app.log`. | Done [test_security] |
| 13 | Validate inputs server-side | Every field is type- and length-checked; hashtags, dates, post types, file types, counts. | Done [test_posts] |
| 14 | Sanitize user content | Captions are stored as plain text; the front end never injects HTML (a test fails if `innerHTML` appears); the CSP forbids inline scripts. Spreadsheet-formula characters are neutralised in the CSV export. | Done [test_posts] |
| 15 | Secure file uploads | Extension allowlist, content sniffing (a renamed program is refused), extension/content match, size cap, `ffprobe` must accept it, random stored names, path-traversal guard, files outside any served folder. | Done [test_posts] |
| 16 | Prevent SQL / NoSQL injection | Only parameterized queries; no NoSQL. | Done |
| 17 | Rate-limit login and signup | 8 attempts per 10 minutes per address and per username; sign-up does not exist. Upload, assistant, generation and agent calls are also limited. | Done [test_security] |
| 18 | Check Git history for secrets | `python scripts/security_preflight.py` scans the tree and full history; run before the first push. | Done (script) |
| 19 | Add security headers, restrict CORS | CSP, nosniff, frame denial, no referrer, permissions policy (microphone for this site only), HSTS over https. No CORS unless you list origins; `*` is refused at start-up. Host header check blocks DNS-rebinding. | Done [test_security] |

## Extra protections specific to this app

- **Approval integrity.** Approvals are bound to file and caption hashes and verified again at publish time; a tampered file is refused [test_posts].
- **Public media link.** Random 24-byte token, 30-minute life, deleted after publishing, served from a separate port that has no other routes [test_runtime].
- **Voice.** Speech text goes to the PC's speech tool through standard input, never a command line [test_misc]. Confirmations are single-use, expire, are bound to the owner and the exact content [test_assistant].
- **AI text.** Post titles, briefs and captions are fenced as data in the assistant's prompt; actions are a whitelist; model output is parsed and validated [test_assistant, test_misc].
- **FFmpeg.** Argument lists only; file names are generated; caption text is drawn by Pillow, never passed to FFmpeg.
- **Instagram token.** Stays server-side. If it leaks: revoke it in the Meta developer dashboard, create a new one, update `.env`.

## Things you must do yourself

- Keep `HOST=127.0.0.1` unless you need the local network; use https for phone access (`docs/REMOTE_ACCESS.md`).
- Set `SESSION_COOKIE_SECURE=1` when serving over https.
- Point tunnels only at the media port (5058), never at 5057.
- Keep `DRY_RUN=1` until you have done a supervised first post.
- Never share `.env`; run the pre-flight before pushing code anywhere.

## Known limits

- The rate limiter and pending confirmations reset or expire on restart (by design for a single-owner app).
- Browser speech recognition may send audio to the browser vendor's service (Chrome sends it to Google).
- Password reset is done at the PC with `python manage.py set-password`; there is no email recovery.
