# Project Memory

Current state. Read this first in every new session, and update it after every task.

## Current status

Version 0.2.0 built and tested (73 automated tests, real FFmpeg, simulated Instagram). Not yet run on the owner's own Windows PC or against the real Instagram account.

## Working

Live board and activity stream, assistant (chat and voice), brief to draft with or without an AI key, uploads and conversion, Swishy inbox, approval gate, dry-run and live publishing (simulated), scheduler, background workers, autostart commands, PC speech, Telegram alerts, agent API, security baseline.

## Waiting on the owner

- First run on Windows: `setup.bat`, `run.bat`, `autostart.bat` (docs/SETUP_CHECKLIST.md)
- Instagram Business or Creator account, Meta developer app, access token
- Tunnel address for the media port
- Optional: AI provider key, Telegram bot, brand colours and name

## Known limits

- Instagram, the AI providers, Telegram, browser speech and Windows autostart are untested against the real services.
- Voice on a phone needs https (docs/REMOTE_ACCESS.md).
- Odia speech recognition depends on the browser.
- Reel length and other Instagram limits in the format checks are guidance; confirm against Meta's current documentation.

## Next steps

Do the first-run checklist; report anything that fails with the text on screen or the last lines of `instance/logs/app.log`.
