# Student Location Tracker 1.0.0 Release Notes

## Highlights
- Dual authentication: traditional login plus optional Google OAuth with post-OAuth profile completion.
- Real-time geolocation with reverse geocoding, live vs. last-active map views, and student location history.
- Attendance tracking via clock in/out with automatic daily time totals.
- Full class management: create/edit, capacity and enrollment toggles, enrollment workflows, and rosters.
- Notification platform with types, preferences, in-app center, badge polling, and broadcast/test tools.
- In-app chatbot assistant for navigation, help, and professor tools.
- Dark/light theme toggle and refreshed UI across dashboards, classes, and notifications.

## New & Improved

**Authentication & Onboarding**
- Student/professor registration with identifier validation; login accepts username/email/ID.
- Google OAuth integration with graceful disablement when not configured.
- Post-OAuth profile completion flows for missing IDs/usernames/metadata.
- “Impossible CAPTCHA” appears after the first failed password attempt to steer toward OAuth.

**Location & Attendance**
- Student dashboard maps current position with accuracy rings; history map shows past check-ins with city/timestamp.
- Reverse geocoding for city names; fallback to “Unknown” on failure.
- Heartbeat endpoint marks students “live” (3-minute window) for professor map filtering (live-only vs all).
- Clock in/out API and UI record coordinates/timestamps and roll up per-day campus time.
- Students can clear their own location history; professors can clear real locations while preserving demo data.

**Classes**
- Professors can create/edit classes with capacity, credits, meeting days, schedule, room, and enrollment-open toggle.
- Students can browse classes, view availability/full/closed status, enroll/drop, and see enrollment counts/spots.
- Class detail pages tailored per role; roster view for professors.
- Optional sample data for professors/classes to demo the experience.

**Notifications**
- Notification types, priorities, icons, and defaults seeded (class reminders, attendance, location, emergency, system, enrollment).
- In-app notification center with filters, unread badge polling, mark-all-read, stats, cleanup, and deletion endpoints.
- User preferences for channels (browser push, in-app, email placeholder), quiet hours, class reminders, and alerts.
- Push subscription endpoints (logging-only delivery stub), broadcast/test senders, and scheduled dispatch support.

**Chat Assistant**
- Embedded chat widget with quick actions and intents for location help, classes, dashboard navigation, professor tools, and logout guidance.

**UX & Theming**
- Dark/light theme toggle with smart positioning per page.
- Refreshed dashboards, class cards, and notification layouts; consistent navigation with badges.

**Operations & Security**
- SQLite/bootstrap helper (`scripts/setup_database.py`) respects `DATABASE_URL` and prepares paths.
- ProxyFix enabled and HTTPS-preferred scheme for deployments behind reverse proxies.
- Security policy documented in `SECURITY.md`; OAuth setup guide in `OAUTH_SETUP.md`.

## Notes & Considerations
- Reverse geocoding requires outbound network access; city names fall back gracefully if blocked.
- OAuth login requires configured `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`; otherwise traditional login remains available.
- Browser push delivery is stubbed to logging; wire to a web push service (e.g., pywebpush + VAPID keys) for production.
- Sample demo locations remain after professor “clear real locations” to keep the map populated for demos.

## Getting Started
- Python 3.11+, `pip`, and internet connectivity recommended.
- Install deps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Initialize DB: `python scripts/setup_database.py` (or `flask --app app db upgrade` if using migrations).
- Run: `flask --app app run --debug` (or `python app.py`).


