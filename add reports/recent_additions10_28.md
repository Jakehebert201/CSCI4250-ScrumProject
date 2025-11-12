# Recent Additions — Oct 28, 2025

Highlights from the modular refactor and onboarding improvements.

## Application factory + modules
- Broke the old monolithic `app.py` into a `studenttracker/` package with a `create_app()` factory.
- Centralized extensions (`SQLAlchemy`, `Migrate`, `OAuth`) and middleware for cleaner imports and easier testing.
- Split routes into dedicated modules (`auth`, `dashboards`, `api`) and gathered helpers in `utils.py` for reuse.

## Template/static discovery fix
- Explicitly pointed Flask at the project-level `templates/` and `static/` directories so deployments outside the repo root pick up assets correctly.

## Hard `/app` mount
- Registered every blueprint with a `/app` URL prefix so generated links always include the deployment path without relying on `X-Forwarded-Prefix`.
- Simplified proxy configuration to the standard host/proto headers; the root route now redirects to `/app/` automatically.

## Seed users for quick demos
- Added automatic creation of `student1` and `professor1` (password `1234`) during app startup to streamline local testing after database resets.

## Documentation refresh
- Updated the README project structure to match the new package layout and mentioned the default login credentials.
