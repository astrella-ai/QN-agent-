# Product Requirements Document

PRD = WHAT and WHY.

## Product

IG Content Agent

## Problem

Making Instagram content is slow and manual: come up with an idea, write copy, build or edit the visual, check the format, write a caption, upload. Doing this consistently takes hours per post.

## Target user

The founder / account owner: one person running one Instagram account, working mostly from a phone and laptop, who wants an agent to do the work but stay in control of what gets posted. (Multi-user is out of scope, but the data model is built to allow it later.)

## Goal

Turn a short brief ("post about X") into a finished, correctly formatted Instagram post that the owner reviews and approves in one place, then publishes it through the official Instagram API.

## Core pipeline

1. Brief intake
2. Script, caption and hashtags
3. Visual: import an export from Swishy (or another editor), or render one in code
4. Format check against Instagram's requirements
5. Approval: preview, edit, approve or reject
6. Publish via the Instagram Graph API
7. Log the result

## MVP

- Owner login (protected dashboard)
- Brief intake form
- Caption, hashtag and short script generation
- Asset import: upload, or drop a Swishy export into an inbox folder
- FFmpeg-based normalize and validate (vertical 1080x1920 MP4 for Reels)
- Code-rendered simple videos from text and images (kinetic text, slideshow with captions)
- Approval inbox with phone-shaped preview, caption editing, approve / send back / reject
- Publish a Reel to the owner's Instagram Professional account, then single image and carousel
- Activity log and per-post result record
- DRY_RUN mode that does everything except the final publish call

## Out of scope for version 1

- Automating Swishy's website through a browser (no public API found; exports are imported instead)
- Posting without approval
- Comment or DM automation, analytics dashboards
- Multiple Instagram accounts or multiple users
- Cross-posting to TikTok, YouTube, WhatsApp, Telegram
- Post scheduling calendar (a simple "publish after approval" only)
- Paid ads, shopping tags
- Voice control and a mobile app

## Success criteria

The owner can:

1. Log in to the dashboard and nobody else can see it.
2. Submit a brief and receive a draft caption and hashtags.
3. Add a video (uploaded or from the Swishy inbox) and see it pass or fail the format check with a clear reason.
4. Preview the post exactly as it will be sent, edit the caption, and approve it.
5. Publish it to Instagram and see the post link and status in the log.
6. Confirm that a post that was never approved cannot be published by any route or tool.

## Constraints

- Free or low-cost tooling wherever possible; paid tools only after a proposal and approval.
- Requires an Instagram Business or Creator account linked to a Meta developer app.
- Official Instagram Graph API only.
- Must run on the owner's own machine first; hosting comes later.

## Open questions (need the owner's answer)

1. What kind of content comes first: animated text and graphics, edited clips of own footage, or photo carousels?
2. Is the Instagram account already Business or Creator, and linked to a Facebook Page?
3. Which Swishy plan (if any) will be used, and is manual export acceptable for v1?
4. Where will media be hosted so Instagram can fetch it (see ADR-006)?
5. Which LLM provider should generate captions and scripts?
6. Brand kit: colours, fonts, logo, tone of voice (see `docs/DESIGN.md`).
