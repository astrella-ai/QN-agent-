# Product Requirements Document (v2)

PRD = WHAT and WHY.

## Product

IG Content Agent: a local app, used from a PC and a phone, that makes Instagram content with the owner and publishes only what the owner approves.

## Problem

Making Instagram content is slow and manual: idea, copy, visual, format check, caption, upload. Doing it consistently takes hours per post, and mistakes (wrong format, wrong caption, posting something unapproved) are public.

## Who it is for

The founder / account owner: one person, one Instagram account, working from a PC and a phone, comfortable talking in English, Hindi or Odia, who wants the agent to do the work and stay in control of what goes public.

## Goal

From a short brief (typed or spoken) to a correctly formatted post that the owner reviews on a live screen and approves, then publishes through Instagram's official API, with the agent starting by itself, working in the background, and talking the work through with the owner.

## What version 2 delivers

- Live screen: board and activity feed that update in real time on PC and phone (installable web app)
- Assistant with voice and chat: spoken briefing on activation, spoken and typed conversation about the work, safe actions by command, confirmation by tap for approve, publish and reject
- Starts by itself at sign-in; background workers keep running; jobs survive restarts
- Brief to draft: caption, hashtags and a built text video, with or without an AI key
- Uploads: validated by content, size-limited, converted to Instagram format; Swishy exports picked up from an inbox folder
- Approval gate bound to the exact media and caption, checked again at publish time
- Publishing: Reel, image, story and carousel through the Graph API; dry-run mode (default); retries; daily-limit check; scheduled posts
- Notifications: on-screen, browser, PC speakers (optional), Telegram (optional)
- Automation-agent API that can draft and read but never approve or publish
- Security baseline from the 19-point checklist

## Out of scope

- Automating Swishy's website through a browser (no public API found; exports are imported)
- Posting without approval, including "autopilot"
- Comments, direct messages, analytics
- Multiple Instagram accounts or multiple people
- TikTok, YouTube, WhatsApp posting
- Native Android or iOS apps (the web app installs on both)
- Cloud hosting (it runs on the owner's PC)

## Success criteria

1. Setup takes one double-click and three questions; the app is running and reachable.
2. A brief produces a reviewable post in about a minute with no AI key.
3. The board updates without a refresh while work happens.
4. Pressing the orb produces a correct spoken briefing and the assistant can start a post.
5. After signing out and in to the PC, the app is already running.
6. A fake or oversized file is refused with a clear reason; a real one is converted.
7. A post that was never approved, or changed after approval, cannot be published by any route, voice command or agent call.
8. In dry-run mode nothing reaches Instagram.

## Constraints

- Free or low-cost tooling; paid tools only by the owner's choice
- Instagram Business or Creator account and a Meta developer app for live posting
- Official Instagram API only
- Works on Windows first; macOS and Linux supported

## Open items (need the owner)

1. Instagram account type, Meta app, and access token (live posting)
2. Permanent tunnel address for media (live posting)
3. Which AI provider, if any
4. Brand kit for rendered videos (colours, name); defaults are neutral
5. Which content types matter most; text videos and Swishy exports are supported first
