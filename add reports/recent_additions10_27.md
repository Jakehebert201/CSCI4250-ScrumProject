# Recent Additions

Snapshot of notable updates so contributors can see what changed at a glance.

## Prefix-aware routing (Oct 27, 2025)
- Added `PrefixMiddleware` alongside `ProxyFix` so production paths under `/app` work without touching templates.
- Middleware auto-detects forwarded headers (`X-Script-Name`, `X-Forwarded-Prefix`) and falls back to an `APP_URL_PREFIX` env var. The app now defaults to `/app`; export `APP_URL_PREFIX=/` if you want to run at the site root locally.
- README and `recent_changes_102525.md` updated to explain the configuration knobs.

## Dynamic drop-in pages (Oct 25, 2025)
- Introduced the `/app/<slug>/` generic route with slug sanitization and manifest-driven navigation.
- Added `scripts/new_page.py` plus `pages.json` for quick scaffolding of new pages; base layout (`templates/base.html`) renders the manifest automatically.
- Seeded sample pages (`faculty-dashboard`, `student-lookup`) and documented the workflow in `recent_changes_102525.md`.

For deeper context, read `recent_changes_102525.md` or the relevant README sections; this file stays focused on the high-level highlights.
