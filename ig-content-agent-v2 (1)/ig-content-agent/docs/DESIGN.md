# Design System (v2)

DESIGN.md = how it should look and feel.

## Job of the screen

The dashboard has one job: let the owner see what is happening, judge a finished post quickly, and approve or send it back. It is a control room, not a marketing page. The memorable element is the phone-shaped preview with an optional safe-zone overlay.

## Tokens

Set as CSS variables in `app/static/app.css`; light and dark variants follow the device.

| Token | Light | Use |
|---|---|---|
| `--bg` | `#F2F4F6` | Page |
| `--panel` | `#FFFFFF` | Cards |
| `--text` | `#1B2430` | Text, primary button |
| `--muted` | `#5B6673` | Secondary text |
| `--approve` | `#1F7A5C` | Approve, success, "listening ready" |
| `--hold` | `#B7791F` | Preparing, warnings, thinking |
| `--stop` | `#B23A48` | Reject, errors, listening |
| `--focus` | `#2F5DA8` | Focus ring, speaking |

Type: the device's own font (system UI stack including Noto Sans Devanagari and Noto Sans Oriya, Nirmala UI on Windows), so Hindi and Odia text always renders and nothing is loaded from the internet. Sentence case. 8 px radius.

## Screens

- **Live:** counts strip (Need you, Preparing, Going out, Done, Problems), five board columns, and an activity feed that fills in live. On a phone the columns stack and navigation moves to a bottom bar.
- **Post:** phone preview left, decisions right (caption with live character count, hashtags, schedule, media tools, checks, actions). Safe-zone overlay marks roughly the top 13% and bottom 18% of the frame; verify against Instagram's current interface.
- **New post:** brief, type, visual mode, optional files.
- **Settings:** system status with clear OK / Check / Fix marks, voice options, notifications, log export, sign out.
- **Assistant panel:** slides in from the right (full screen on phone). Messages, a confirm card, a mic button, a text box.

## The orb

One shape shows the assistant's state everywhere: green ready, red pulsing listening, amber pulsing thinking, blue pulsing speaking. The status line under it says the same in words. Motion stops for people who prefer reduced motion.

## Principles

- Show what will be sent: the same file and caption that were approved. Editing resets approval visibly.
- Anything public needs a deliberate tap with a plain-language dialog. In dry-run mode the dialog and buttons say so ("Approve and dry run", "Nothing will be posted").
- Errors say what happened and what to do next.
- The screen never needs a manual refresh; a "Live updates on / Reconnecting" pill shows the connection.
- Keyboard focus is always visible; touch targets are at least 44 px; text and controls work at 375, 768 and 1440 px.

## Copy

Buttons say what happens: "Approve and publish", "Send back for edits", "Remove from board". One word per idea across the app.

## Video design (rendered text videos)

1080x1920, 30 fps, H.264 and AAC. Large centred text with a short fade and rise, a thin progress bar, optional brand name. Colours from `BRAND_BG`, `BRAND_FG`, `BRAND_ACCENT` in `.env`.
