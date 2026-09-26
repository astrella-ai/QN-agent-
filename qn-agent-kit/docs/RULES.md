# Development Rules

## General
- Use TypeScript.
- Reuse existing components.
- Do not duplicate logic.
- Keep functions small.
- Do not modify unrelated files.

## Before Coding
- Read the relevant project documentation.
- Inspect existing implementation.
- Reuse existing functionality where possible.
- Make a plan for large changes.

## UI
- Follow DESIGN.md.
- Maintain responsive design.
- Include loading states.
- Include error states.
- Include empty states.

## Security
- Never expose API keys.
- Validate user input server-side.
- Verify authorization server-side.

## Integrations
- Every third-party platform lives in its own service file.
- Never call third-party APIs directly from UI components.
- Check INTEGRATIONS.md before adding any new external dependency.

## Testing
- Add tests for important functionality.
- Run tests after implementation.
- Fix failing tests before continuing.

## Git
- Make small commits.
- Use descriptive commit messages.
