# Test Plan (v2)

Run everything: `python -m unittest discover -s tests` (uses real FFmpeg; takes a few minutes). Automated tests live in `tests/`.

| File | What it proves |
|---|---|
| `test_security.py` | Sign-in, CSRF, logged-out access, headers, no open CORS, host-header (rebinding) block, login rate limit, generic errors, data isolation, agent token limits, refusal to start with unsafe settings |
| `test_posts.py` | Brief to reviewable post with no AI key; approval bound to exact content; no publish without approval; dry run posts nothing; tampered file refused; validation; uploads (fake file, wrong extension, size, real video and image conversion, carousel limit, path traversal, API auth and CSRF) |
| `test_publisher.py` | Live publishing against a simulated Instagram: exact parameters, token never in URLs or records, retries, daily limit, processing errors, carousels, missing setup explained |
| `test_assistant.py` | Briefing accuracy, voice commands, confirmation required, single use, expiry, owner binding, change-after-ask refusal, AI actions whitelisted, untrusted text fenced, outage fallback |
| `test_runtime.py` | Inbox pick-up and rejection, scheduler, restart recovery, background workers doing the whole pipeline, live event stream over a real socket, public media server |
| `test_misc.py` | Setup writes a hash and never the password, autostart definitions, single-instance check, PC speech via stdin, quiet hours, AI provider request formats, log redaction, `.env.example` |

## Checked by hand (needs your devices or accounts)

See `docs/SETUP_CHECKLIST.md`: a real Instagram post, an AI provider key, Telegram, browser microphone and voices on your PC and phone, Windows autostart and PC speech, the tunnel to port 5058.

## Layout checks (by hand, in the browser)

At 375, 768 and 1440 px: the board, the post page, the assistant panel and Settings are usable; the bottom navigation appears on phones; keyboard-only approval works and focus is visible.

## Before every release

`python manage.py doctor`, the full test suite, and `python scripts/security_preflight.py` all pass.
