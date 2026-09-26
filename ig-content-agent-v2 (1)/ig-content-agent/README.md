# IG Content Agent

A working app for your PC (and your phone) that turns a short brief into a finished Instagram post, shows it to you on a live screen, talks with you about the work, and publishes only what you approve.

**idea → caption and script → video (built here, or exported from Swishy) → format check → your approval → publish → log**

What you get:

- **Live screen.** A board that updates by itself while the agent works: preparing, needs you, going out, done, problems. A live activity feed beside it.
- **Assistant that talks.** Press the orb: it greets you with a spoken briefing, then you can talk or type: "status", "new reel about morning routines", "approve post 4". Approving, publishing and rejecting always need a tap on a confirm card.
- **Starts by itself.** One command makes it start every time you sign in to the PC. It can also speak a briefing on the PC's speakers at start.
- **Uploads that hold up.** Every file is checked by its real content, size-limited, given a random name, then converted to Instagram's format (1080x1920 H.264 for Reels). Drop a Swishy export into the inbox folder and it becomes a draft post on its own.
- **Runs on PC and phone.** Same app in both. On the phone it installs like an app (Add to Home screen).
- **Safe by default.** Dry run is on: everything happens except the final post. Nothing is posted without your approval of the exact video and caption.

## Start here (Windows)

1. Install Python 3.11 or newer from python.org (tick "Add python.exe to PATH").
2. Double-click **`setup.bat`**. It creates the environment, installs the requirements, asks you to choose a username and password, and checks your setup. If it says FFmpeg is missing, run `winget install Gyan.FFmpeg` and reopen the window.
3. Double-click **`run.bat`**. Your browser opens the dashboard at http://localhost:5057.
4. Double-click **`autostart.bat`** once so it starts by itself at every sign-in.

Mac or Linux: `./setup.sh`, then `./run.sh`, then `python manage.py install-autostart` from the `.venv`.

## Use it

- **New post:** write a brief. The agent writes the caption and hashtags and builds a text video. You review it on the phone-shaped preview and approve.
- **Your own video or image:** upload it on the post, or drop it in `instance/inbox/`.
- **Talk to it:** press the orb at the top. See `docs/VOICE.md` for languages and limits.
- **Go live for real:** see the checklist below. Until then it is a dry run.

## Use it from your phone

Read `docs/REMOTE_ACCESS.md`. Short version: install Tailscale on the PC and the phone, expose the app over https, and open it in Chrome. Voice on a phone needs https.

## Before real posting

1. Instagram account must be Business or Creator, linked to a Facebook Page.
2. Create a Meta developer app, get `IG_USER_ID` and a long-lived `IG_ACCESS_TOKEN`, put them in `.env`.
3. Start a tunnel to the **media port** (5058) and set `PUBLIC_MEDIA_BASE_URL`. Instagram downloads your video from there. The dashboard is never exposed.
4. Run `python manage.py doctor`, then change `DRY_RUN=1` to `DRY_RUN=0` in `.env` and restart.
5. First live post: approve it yourself and watch the activity feed.

## Your automation agent

`python manage.py agent-token` creates a separate key. With it your agent can create drafts and read status through `/api/agent/*`. It cannot approve or publish. Only you can, in the dashboard.

## Commands

| Command | What it does |
|---|---|
| `python manage.py init` | First-time setup (secret key, password hash) |
| `python manage.py doctor` | Checks Python, packages, FFmpeg, settings |
| `python manage.py run --open` | Starts everything |
| `python manage.py install-autostart` | Start at sign-in (`remove-autostart` undoes it) |
| `python manage.py set-password` | Change the password |
| `python manage.py agent-token` | Key for your automation agent |
| `python -m unittest discover -s tests` | Run the 73 automated tests |
| `python scripts/security_preflight.py` | Secret and config scan before commits |

## What is tested, and what is not

Tested here (automatically, with real FFmpeg): sign-in and CSRF, isolation between users, uploads, conversion, the approval rules, dry-run and live publishing against a simulated Instagram, retries, the inbox, the scheduler, the background workers, the live event stream, the assistant, and the launch path.

**Not tested against the real services** because they need your accounts: Instagram itself, your AI provider, Telegram, browser speech on your devices, and Windows autostart and PC speech (built and unit-tested, not run on a Windows machine). Expect to do a first pass on each; `docs/SETUP_CHECKLIST.md` lists them in order.

## Project docs

`docs/PRD.md` what and why. `docs/ARCHITECTURE.md` how it works. `docs/SECURITY.md` the 19-point checklist with status. `docs/DESIGN.md` the look. `docs/TEST_PLAN.md` what is verified. `docs/DECISIONS.md` decisions. `docs/MEMORY.md` current state. `RULES.md` rules for anyone changing the code. `TASKS.md` the task list.
