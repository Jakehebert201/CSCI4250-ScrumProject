# Recent Changes — October 25, 2025

This document captures the major updates introduced to support “drop‑in” content pages under the `/app/<slug>/` URL space and the tooling that powers them.

## 1. Dynamic Page Routing (`app.py`)
- **Path constants**: At import time we define `BASE_DIR`, `PAGES_DIR`, and the path to `pages.json` so every helper uses a single source of truth.
- **Manifest loader**: `_load_pages_manifest()` reads `pages.json` once, logging (but not crashing) if the file is missing or malformed. The resulting list is stored in `PAGES_MANIFEST`.
- **Template context**: `@app.context_processor` now injects `pages_manifest` so *any* template can iterate the generated navigation without additional plumbing.
- **Slug normalization**: `_normalize_slug()` trims leading/trailing slashes, rejects empty strings, and bails if any path segment is `.` or `..`.
- **Secure renderer**: The `/app/<path:slug>/` route validates the normalized slug, ensures the resolved file lives inside `templates/pages/`, and aborts with a 404 if the file is missing or out of bounds before calling `render_template`. This matches the README promise about sanitized slugs.

**Operational note:** Because the manifest is cached at import time, restart the Flask/Gunicorn process (e.g., `docker compose restart app`) whenever `pages.json` changes.

## 2. Base Layout & Generated Templates
- Added `templates/base.html`, a shared layout that loads `static/css/style.css` via `url_for`. The header iterates `pages_manifest` to auto-render nav links for every entry in the manifest. When no pages exist, a muted placeholder appears instead.
- Seed files in `templates/pages/` (`faculty-dashboard.html`, `student-lookup.html`) demonstrate how generated pages simply extend `base.html` and provide content blocks.

## 3. Page Manifest (`pages.json`)
- New JSON manifest listing objects shaped like `{ "slug": "faculty-dashboard", "title": "Faculty Dashboard" }`.
- Acts as the single place to describe drop-in pages so the nav, tooling, and doc examples stay in sync.

## 4. Generation Script (`scripts/new_page.py`)
- CLI usage: `python scripts/new_page.py my-page "My Page"`.
- Behavior:
  1. Sanitizes/slugifies the first argument (lowercase, spaces → dashes, strips `..` and `/`).
  2. Builds `templates/pages/<slug>.html` from a stub that extends `base.html` and timestamps the generation.
  3. Appends a title entry to `pages.json` (creating the file if it does not exist) while preventing duplicates.
  4. Prints the relative paths touched for easy git add/commit workflows.
- Script is executable (`chmod +x`) so it can also be invoked directly (`./scripts/new_page.py …`).

## 5. README Updates
- Project structure now lists the base layout, pages directory, manifest, and script.
- “Key Routes” includes `GET /app/<slug>/`.
- New “Dynamic Page Workflow” section documents routing, manifest-driven navigation, the scaffolding command, bulk-generation hints, and the reminder to restart the app after manifest edits.

## 6. Testing/Validation
- `python3 -m py_compile app.py scripts/new_page.py` run locally to ensure syntax integrity.
- Manual spot checks confirmed the sample drop-in pages load through the new route.

These changes collectively deliver the “drop a file → page is live” experience while keeping routing safe and tooling documented for other contributors. Commit `templates/pages/<slug>.html` alongside `pages.json` whenever you add new content via the script.

## 7. Prefix-Aware Deployment (Follow-up)
- Added `werkzeug.middleware.proxy_fix.ProxyFix` plus a lightweight `PrefixMiddleware` to honour the `/app` mount point used by nginx. Requests arrive with `/app/...` in `PATH_INFO`, the middleware trims the prefix for internal routing, and `SCRIPT_NAME` is set so all `url_for` calls emit `/app/...` URLs automatically.
- Middleware now autodetects prefixes via `X-Script-Name`/`X-Forwarded-Prefix` headers and falls back to an optional `APP_URL_PREFIX` environment variable. Leave it unset for local dev (routes stay `/dashboard`, `/static/...`); production can either forward headers from nginx or export `APP_URL_PREFIX=/app`.
- This approach keeps the application agnostic to deployment specifics: templates stay clean, and changing the public prefix is as simple as updating the middleware configuration or the forwarded `X-Script-Name` header.
