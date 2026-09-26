# Security Requirements

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
