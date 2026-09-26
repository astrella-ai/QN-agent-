# Security Requirements

## PC Action Permission Tiers (non-negotiable — applies to every phase, every feature)
This is the actual safety boundary for this agent, since it's designed to act on a real PC and
eventually control a screen. It does not get relaxed later "once it's trusted."

- **Tier 1 — auto, no confirmation:** read-only or trivially reversible (search, read a file, take a
  note, answer a question)
- **Tier 2 — confirm-lightweight:** changes state but is easy to undo (write a new file, open an
  app) — one quick confirm, not a full interrogation
- **Tier 3 — confirm-explicit, every single time, no exceptions, ever:** delete anything, spend
  money, install at the system level, act on another account or service, send a message/email on
  Snehasis's behalf, touch credentials

Rules that apply regardless of phase or how "trusted" the agent becomes:
- A Tier 3 action never executes without an explicit, specific confirmation for that exact action —
  a standing "yes, always allow this" is not valid for Tier 3.
- The agent never works around a paywall, license restriction, or payment requirement on its own —
  it reports "this needs a subscription/login/payment" and waits for Snehasis, every time.
- No action tier is ever downgraded by a feature request, a deadline, or a "just this once."

## Secrets
- All API keys live in `.env.local`, never in source code.
- `.env`, `.env.local` are in `.gitignore` from the first commit.
- Only truly public values (e.g. a public anon key) may be exposed client-side.

## Authentication & Authorization
- Every private route checks a valid session server-side.
- Never trust a user ID sent from the frontend — derive it from the verified session.
- Every read/write checks resource ownership, not just login status.
- Database-level access policies (e.g. Supabase RLS) on every table.

## Errors & Debugging
- Production disables verbose logging, stack traces, debug panels.
- Client sees generic error messages; details are logged server-side only.

## Input & Uploads
- All input validated server-side, regardless of client-side validation.
- User-generated content sanitized before rendering.
- File uploads validated by content type, size, and given safe filenames.

## Injection Prevention
- Parameterized queries / ORM only — never string-concatenated queries.

## Rate Limiting
- Login, signup, and password-reset endpoints are rate-limited.

## Before Going Public
- Run a secrets scanner (e.g. gitleaks) on the full Git history.
- Rotate any credential that was ever committed, even if since removed.
- Set security headers (CSP, X-Frame-Options, HSTS, X-Content-Type-Options).
- Restrict CORS to actual frontend origin(s) in production.
