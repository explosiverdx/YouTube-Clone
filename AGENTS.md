# AGENTS.md

## Cursor Cloud specific instructions

This is a client-side-only React app (Create React App) — a YouTube clone called "JSM Media". There is no backend server, no database, and no monorepo structure.

### Quick reference

| Action | Command |
|--------|---------|
| Install deps | `npm install` |
| Dev server | `npm start` (port 3000) |
| Build | `npm run build` |
| Lint | `npx eslint src/` |
| Test | `CI=true npm test -- --passWithNoTests` |

### Key notes

- The app requires a valid `REACT_APP_RAPID_API_KEY` in `.env` to fetch video data from `youtube-v31.p.rapidapi.com`. Without a valid key, the UI loads but all API calls return errors (typically 429 or 403). The `.env` file is committed with a key that may be rate-limited or expired.
- There are no automated tests in the codebase. Running `npm test` with `--passWithNoTests` avoids a non-zero exit code.
- The build produces a minor autoprefixer CSS warning about `start` vs `flex-start` — this is harmless.
- Use `BROWSER=none` when starting the dev server to prevent attempting to open a browser: `BROWSER=none npm start`.
