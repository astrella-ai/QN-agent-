# Voice and the assistant

## How it works

- **Activate:** press the orb at the top. It speaks a short briefing about what needs you, then listens. Say what you want, or type.
- **Understanding:** without an AI key it understands a set of commands. With `LLM_PROVIDER` and `LLM_API_KEY` set it holds a free conversation about your work (in English, Hindi, Odia or a mix, as far as the model supports), using the live state of your posts.
- **Doing:** it can start a post, write a caption, build a text video, edit a caption, schedule, and open a post. It cannot approve, reject or publish by itself: those show a confirm card, and you tap Confirm. The card is tied to the exact video and caption you saw; if either changes, it refuses.
- **Stopping:** say "stop", "bye" or "cancel", press Stop, or close the panel. After a few seconds of silence it stops listening.

## Where the speech happens

| Part | Where | Notes |
|---|---|---|
| Listening (speech to text) | Your browser | Chrome and Edge work. In Chrome the audio goes to Google's speech service, so it needs internet. Firefox and Safari differ or do not support it; typing always works. |
| Speaking (text to speech) | Your browser | Uses the voices installed on your device. Pick language, voice and speed in Settings. |
| Speaking on the PC's speakers | The app on the PC | Optional: `LOCAL_TTS=1`. Used for alerts and, with `TTS_ON_START=1`, a short briefing when the app starts by itself. Windows uses the built-in voice, macOS uses `say`, Linux needs `espeak-ng`. `QUIET_HOURS=22-7` keeps it silent at night. |

A browser cannot speak by itself before you have touched the page once; that is a browser rule. That is why the start-up briefing on the PC uses the PC's own speech instead.

## Languages

Settings offers English (India), Hindi, Odia, English (US) and English (UK). Odia listening is not supported by every browser; if it is not, the panel says so and you can type in Odia instead. Rendered text videos use system fonts; on Windows the built-in Nirmala UI font covers Hindi and Odia.

## Privacy

Voice settings are stored only in your browser. Your conversation is stored in the app's local database on your PC (`instance/app.db`). If you set an AI provider, the text of your message and a short summary of your posts is sent to that provider to produce a reply.
