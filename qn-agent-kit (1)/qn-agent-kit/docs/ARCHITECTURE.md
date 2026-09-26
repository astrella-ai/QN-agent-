# Architecture

## Frontend
[e.g. Next.js + TypeScript]

## Styling
[e.g. Tailwind CSS]

## Backend
[e.g. Next.js server actions / separate API]

## Database
[e.g. Supabase PostgreSQL]

## Authentication
[e.g. Supabase Auth]

## Deployment
[e.g. Vercel]

## Data Flow
User → UI → Server Action / API → Database → back to UI

## Folder Structure
```
src/
├── app/
├── components/
├── features/
├── services/
├── lib/
├── types/
└── utils/
```

## Architectural Rules
- UI components must not contain database logic.
- Database operations belong in `services/`.
- Authentication must be verified server-side.
- Third-party integrations get their own service file (see INTEGRATIONS.md) — never called directly from UI.
- Business logic stays separate from UI.
