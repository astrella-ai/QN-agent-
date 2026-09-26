# Design System

DESIGN.md = how it should look and feel. Two things are designed here: the approval dashboard, and the videos the agent makes.

## Subject and job

The dashboard's one job: let the owner judge a finished post quickly and confidently, then approve or send it back. It is a review desk, not a marketing site. The distinctive thing is the phone-shaped preview.

## Dashboard tokens

Colours

| Name | Hex | Use |
|---|---|---|
| Ink | `#1B2430` | Text, primary buttons |
| Proof | `#F2F4F6` | Page background |
| Sheet | `#FFFFFF` | Panels |
| Approve | `#1F7A5C` | Approve action, success states |
| Hold | `#B7791F` | Needs edits, warnings |
| Stop | `#B23A48` | Reject, destructive, errors |

Type: **Instrument Sans** for everything (weights 400, 500, 600); tabular figures for durations and counts. Sentence case throughout. Line length under 75 characters.

Shape: 8px radius on controls, 16px on the phone preview frame only. Panels are separated by whitespace, not borders on everything.

## Layout concept

Left: the phone preview. Right: what to decide.

```
+--------------------------------------------------------------+
|  Review post 14                          Draft  Ready  Done   |
+--------------------+-----------------------------------------+
|  +--------------+  |  Caption                                |
|  |              |  |  [ editable text, live character count ]|
|  |   9:16       |  |                                         |
|  |   preview    |  |  Checks                                 |
|  |   [safe zone |  |  OK  1080x1920, 24 s, H.264/AAC         |
|  |    overlay]  |  |  OK  File size 38 MB                    |
|  +--------------+  |  !   Caption over 2,200 characters      |
|  [ play ] 0:12/0:24|                                         |
|                    |  [ Approve and publish ] [ Send back ]  |
|                    |                          [ Reject ]     |
+--------------------+-----------------------------------------+
```

Alignment: left-aligned. On mobile (375px) the preview stacks above the decision panel and the action buttons stick to the bottom.

## Principles

- The preview is the memorable element; everything else is quiet.
- A toggle shows the safe-zone overlay (where Instagram's interface covers the video). Keep key text clear of roughly the top 250 px and bottom 350 px of a 1080x1920 frame. Verify against Instagram's current interface when building.
- Show exactly what will be sent: same file, same caption. If either changes after approval, the approval visibly resets.
- Failures say what happened and what to do next. No apologies, no vague errors.
- Motion only in response to an action (button pressed, status changed). Respect reduced-motion settings.

## States and accessibility

- Every screen has loading, empty and error states.
- Empty inbox copy: "No posts waiting. Start one from a brief."
- Visible keyboard focus, sufficient contrast, labelled form fields, usable at 375, 768 and 1440 px.

## Copy rules

- Buttons say exactly what happens: "Approve and publish", "Send back for edits", "Reject".
- The same word is used through the whole flow: the button says "Publish", the confirmation says "Published".
- Error example: "Instagram could not fetch the video. The public link expired. Retry to create a new link."

## Video design (for rendered content)

- Format: 1080x1920 (9:16), 30 fps, MP4 (H.264 video, AAC audio).
- Keep text inside the safe zone. Minimum caption text size readable on a phone at arm's length.
- Burn-in captions for any spoken or key text; assume many people watch without sound.
- Brand kit (to be supplied by the owner): logo, two colours, one or two fonts, tone of voice. Until supplied, renderers use a neutral default.
