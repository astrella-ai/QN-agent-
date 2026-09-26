# Integrations

Only what this project's MVP actually needs. (The full researched list from earlier stays available
in the general qn-agent-kit for future projects — copy any of those over here if a later phase needs them.)

---

## Google AI Studio (Gemini)
- **URL:** https://aistudio.google.com/prompts/new_chat
- **Purpose:** Core LLM backend for chat/reasoning
- **Type:** SaaS platform with API
- **Auth needed:** Yes — Google account + API key
- **Cost:** Free tier, paid usage beyond limits
- **Notes:** Called only from src/services/llm.ts (or equivalent) — never directly from UI

---

## Coqui TTS
- **URL:** https://github.com/coqui-ai/tts
- **Purpose:** Text-to-speech for voice output
- **Type:** Open-source library (self-hosted)
- **Auth needed:** No
- **Cost:** Free
- **Notes:** Verify a currently-maintained fork before depending on it — the original commercial arm shut down

---

## Speech-to-text (to be decided)
- **URL:** TBD — evaluating Whisper.cpp / faster-whisper
- **Purpose:** Voice input transcription, ideally local/offline
- **Type:** Open-source library (self-hosted)
- **Auth needed:** No
- **Cost:** Free
- **Notes:** Log the final choice here once picked in docs/DECISIONS.md and here

---

<!-- Add web search provider here once one is chosen for Phase 6 -->
