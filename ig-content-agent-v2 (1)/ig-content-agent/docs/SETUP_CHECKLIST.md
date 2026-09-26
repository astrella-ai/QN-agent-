# First-run checklist

Do these in order. Each has a way to confirm it worked.

1. **Setup and start.** `setup.bat`, then `run.bat`. Confirm: the dashboard opens and the pills at the top say "Worker running".
2. **Make a test post.** New post, type a two-sentence brief, choose Reel and "Make a text video for me". Confirm: within about a minute it appears under "Needs you" with a video you can play.
3. **Dry run.** Open it, press "Approve and dry run". Confirm: it moves to Done as "Dry run done" and the feed says nothing was posted.
4. **Inbox.** Export any video from Swishy (or any phone video) and drop it in `instance/inbox/`. Confirm: a draft post appears by itself and asks for a caption.
5. **Voice on the PC.** Open the app in Chrome or Edge on the PC, press the orb, allow the microphone. Confirm: it speaks the briefing and listens. Say "status".
6. **Start by itself.** Run `autostart.bat`, sign out and in. Confirm: the dashboard is reachable without running anything.
7. **AI writer (optional).** Put `LLM_PROVIDER` and `LLM_API_KEY` in `.env`, restart. Confirm: Settings shows the provider, and "Write caption again" gives real copywriting.
8. **Phone.** Follow `docs/REMOTE_ACCESS.md`. Confirm: sign in from the phone and see the same board.
9. **Instagram.** Follow "Before real posting" in the README. Confirm: `python manage.py doctor` shows the account as connected, then do one supervised live post.
10. **Speak on the PC (optional).** `LOCAL_TTS=1` and `TTS_ON_START=1` in `.env`. Confirm: after restart the PC speaks a short briefing.
