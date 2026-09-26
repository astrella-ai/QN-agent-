# Tasks

`[you]` = needs the owner. Everything else is built and tested.

## Built

- [x] Foundation: config that fails closed, database, sign-in, CSRF, headers, rate limits, host check, generic errors
- [x] Live screen: board, activity feed, event stream, worker heartbeats, installable web app
- [x] Posts: state machine, approvals bound to content, checks, scheduling
- [x] Uploads: content sniffing, limits, conversion to Instagram format, carousel, Swishy inbox
- [x] Text-to-video renderer, caption and hashtag writer (offline and AI providers)
- [x] Assistant: chat and voice, briefing, actions, confirmation cards
- [x] Publisher: dry run, Reel / image / story / carousel, retries, limit check, media link server
- [x] Starts by itself, single instance, restart recovery, PC speech, Telegram alerts
- [x] Agent API (draft and read only)
- [x] Docs, 73 tests, security pre-flight

## To do with you

- [ ] TASK-A [you] Run `setup.bat`, `run.bat`, `autostart.bat` and go through `docs/SETUP_CHECKLIST.md` steps 1 to 6
- [ ] TASK-B [you] Make the Instagram account Business or Creator and link a Facebook Page
- [ ] TASK-C [you] Create the Meta developer app; add your account with a role on it; get `IG_USER_ID` and a long-lived token
- [ ] TASK-D [you] Start the tunnel to port 5058 and set `PUBLIC_MEDIA_BASE_URL`
- [ ] TASK-E [you] Add an AI key if you want free conversation and better captions
- [ ] TASK-F [you] Phone access with Tailscale (`docs/REMOTE_ACCESS.md`)
- [ ] TASK-G [you] One supervised live post, then switch `DRY_RUN=0`

## Later ideas (not built)

- Result log in a Google Sheet
- More templates for rendered videos (audio, image slideshows)
- Analytics after publishing
- Wake-word activation (browsers cannot do this reliably)
