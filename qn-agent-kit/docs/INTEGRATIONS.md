# Integrations

Master list of every external platform, API, app, or open-source tool this project connects to.

---

## Shodan
- **URL:** https://www.shodan.io/
- **Purpose:** Search engine for internet-connected devices — useful for OSINT/security research, infrastructure recon
- **Type:** SaaS platform with API
- **Auth needed:** Yes — API key
- **Cost:** Free tier (limited queries), paid plans for higher volume
- **Notes:** Has a full REST API (`api.shodan.io`) — route this through a dedicated service file, never call directly from UI

---

## start.me — OSINT4ALL
- **URL:** https://start.me/p/L1rEYQ/osint4all?locale=en
- **Purpose:** Curated dashboard/bookmark page of OSINT tools and resources
- **Type:** Curated link collection (not an API)
- **Auth needed:** No
- **Cost:** Free
- **Notes:** This is a directory, not a service to integrate directly — treat as a research reference, not something QN calls programmatically. Worth having QN read it once and pull out the individual tool links it actually needs.

---

## Coqui TTS
- **URL:** https://github.com/coqui-ai/tts
- **Purpose:** Open-source text-to-speech engine — for voice output (relevant to your voice agent projects like Nandi)
- **Type:** Open-source library (self-hosted)
- **Auth needed:** No (runs locally/self-hosted)
- **Cost:** Free, open-source
- **Notes:** Runs on your own infrastructure — no external API calls or vendor lock-in. Check license terms (Coqui's original commercial arm shut down; verify current maintained fork before depending on it for production)

---

## AllGPT
- **URL:** https://allgpt.com/
- **Purpose:** Unified AI workspace aggregating 150+ models (OpenAI, Claude, Gemini, DeepSeek) plus text/image/video/code generation, TTS/STT, in one subscription
- **Type:** SaaS platform
- **Auth needed:** Yes — account login, has integrations with Slack/Notion/Google Workspace
- **Cost:** Paid, starts ~$19.99/mo, free trial available
- **Notes:** Could reduce the need to individually wire in several model APIs — worth deciding if this replaces some other planned integrations rather than sitting alongside them

---

## Kimi K2 (model)
- **URL:** https://www.kimi.ai/ai-models/kimi-k2-6
- **Purpose:** Moonshot AI's Kimi K2 model reference/info page
- **Type:** AI model (via API or kimi.com chat interface)
- **Auth needed:** Yes, for API access
- **Cost:** Check current API pricing at time of integration
- **Notes:** Same underlying provider as the Kimi chat link below — decide if you need API access (for QN to call programmatically) or just the chat UI

## Kimi (chat)
- **URL:** https://www.kimi.com/en
- **Purpose:** Kimi AI chat interface
- **Type:** SaaS chat platform
- **Auth needed:** Yes — account login
- **Cost:** Free tier available
- **Notes:** Chat UI only, not programmatic — fine for manual research, not for QN to call as a tool unless via their API separately

---

## Meigen AI
- **URL:** https://www.meigen.ai/
- **Purpose:** AI prompt gallery for image-generation models (GPT Image, Nano Banana, Seedance, Veo, Midjourney) — searchable prompts, templates, style packs
- **Type:** SaaS platform
- **Auth needed:** Unclear — likely free to browse
- **Cost:** Free (per available info)
- **Notes:** Very new site (registered Jan 2026) — treat as a prompt/reference resource rather than a core dependency until it proves stable

---

## Google AI Studio
- **URL:** https://aistudio.google.com/prompts/new_chat
- **Purpose:** Google's AI Studio — build and test with Gemini models, get API keys
- **Type:** SaaS platform with API
- **Auth needed:** Yes — Google account, API key for programmatic use
- **Cost:** Free tier, paid usage beyond limits
- **Notes:** This is the source for Gemini API keys if any venture needs Gemini specifically

---

## LogoAI
- **URL:** https://www.logoai.com/logo
- **Purpose:** AI logo generator — useful for branding across SYB ventures
- **Type:** SaaS platform
- **Auth needed:** Yes, for saving/downloading
- **Cost:** Free preview, paid to download high-res/full rights
- **Notes:** One-off design tool, not something QN needs deep API integration with — likely just a bookmarked resource

---

## Google Code Wiki
- **URL:** https://codewiki.google/search?q=
- **Purpose:** Google's AI-generated, auto-updating documentation for GitHub repos — architecture diagrams, dependency maps, a Gemini-powered chat agent that understands the whole repo
- **Type:** Free public platform (public preview)
- **Auth needed:** No, for public repos. Private repos need a waitlisted Gemini CLI extension
- **Cost:** Free for public repos
- **Notes:** Genuinely useful for docs/GITHUB_PROTOCOL.md — before QN evaluates a candidate repo, it can check `codewiki.google/github.com/owner/repo` (or search) to get an instant architecture summary instead of manually reading the whole codebase

---

## Mindluster
- **URL:** https://www.mindluster.com/
- **Purpose:** Free online courses platform
- **Type:** SaaS platform (education)
- **Auth needed:** Yes, for course access/certificates
- **Cost:** Free
- **Notes:** Reference/learning resource, not something QN calls programmatically

---

## GitHub
- **URL:** https://github.com
- **Purpose:** Source hosting, and the primary source for repo discovery per docs/GITHUB_PROTOCOL.md
- **Type:** Platform with full API
- **Auth needed:** Yes — personal access token for API/CLI use
- **Cost:** Free for public repos, paid tiers for private/team features
- **Notes:** This is the main one QN interacts with constantly — set up a token with appropriately scoped permissions (not a full-access token) once QN starts actually cloning/searching repos

---

<!-- adescargar.net intentionally excluded — flagged high-risk (modded/cracked Android APK repository) by security scanners. Confirm with the founder before adding. -->
