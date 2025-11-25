# Student Location Tracker

A Flask web app that lets campus staff see student check‑ins on a map, track attendance time, and manage classes. It ships with sample accounts so you can try it immediately.

## Quickstart
- **Requirements:** Python 3.11+, `pip`, and a working internet connection for reverse geocoding.
- **Install deps:**
  ```bash
  python -m venv .venv
  source .venv/bin/activate        # On Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **Configure environment (optional):**
  - Copy `.env.example` to `.env`.
  - Set `FLASK_SECRET` for session signing.
  - Add `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` to enable OAuth login.
  - `DATABASE_URL` overrides the default SQLite file at `instance/studenttracker.db`.
- **Initialize the database (first run):**
  ```bash
  python scripts/setup_database.py       # creates the SQLite file and tables
  # or
  flask --app app db upgrade             # if using migrations
  ```
- **Run the server:**
  ```bash
  flask --app app run --debug
  # or
  python app.py
  ```
- **Open:** http://127.0.0.1:5000
- **Sample logins:** `student1` / `1234` and `professor1` / `1234`

## User Manual
### Students
- **Log in:** Use the sample account or register a new one at `/app/register/student`.
- **Share location:** Visit `/app/dashboard/student`, allow browser geolocation, and the map will update. Location posts to `/app/update_location` and stamps your profile with city + accuracy.
- **Clock in/out:** Use the dashboard buttons; events are saved via `/app/clock_event` and total time accrues automatically per day.
- **Classes:** Browse and enroll from `/app/classes/`; drop from the class page. Enrollment respects capacity and open/closed status.
- **History:** See your recent location points and daily totals in `/app/database`.
- **Clear my locations:** Use the “Clear Locations” action (student-only) if you want to reset your last known coordinates.

### Professors
- **Log in:** Use `professor1` / `1234` or register at `/app/register/professor`.
- **Live map:** `/app/dashboard/professor` shows the latest student positions. “Live” status uses the student heartbeat; toggle between live-only and all points.
- **Classes:** Create and manage classes at `/app/classes/`. Students can enroll; you can edit details, close enrollment, or view rosters.
- **Cleanup tools:** `/app/notifications` > Admin Cleanup lets you clear real locations while preserving demo data. `/app/api/clear-all-locations` also resets last-known positions.
- **Database view:** `/app/database` lists students, professors, classes, locations, and daily time totals for quick auditing.

### Notifications
- Open `/app/notifications` for the inbox. Mark all read, delete, or test-send.
- Preferences live at `/app/api/notifications/preferences` (toggled in the UI): browser push, email, in-app, class reminders, location alerts, quiet hours.
- Broadcast (professors) or per-user notifications go through the notification service; scheduled items are auto-sent when due.

## Feature Highlights
- Password + optional Google OAuth login.
- Real-time geolocation capture with reverse geocoded city names.
- Attendance tracking with clock in/out and per-day totals.
- Class management (capacity, enrollment toggle, rosters).
- Notifications with in-app feed, push subscription support, preferences, and scheduled dispatch.

## Troubleshooting
- **Geolocation denied:** Allow location access in your browser; refresh the dashboard.
- **Database missing:** Re-run `python scripts/setup_database.py` or `flask --app app db upgrade`.
- **OAuth redirect issues:** Ensure the redirect URI matches `/app/oauth/callback` and your domain/port; set both client ID and secret.
- **Reverse geocoding timeouts:** The app falls back to “Unknown”; retry with a stable connection or replace the default Nominatim User-Agent with your contact info in `studenttracker/utils.py`.

## API Reference (JSON)
All API routes are served under the `/app` prefix. Authenticated session cookies are required unless noted.

- `POST /app/update_location` — Save the student’s current position.  
  Body: `{"lat": 33.75, "lng": -84.39, "accuracy": 12.3, "class_id": 1, "notes": "optional"}`  
  Response: `{"success": true, "city": "Atlanta"}` or `401/400`.

- `POST /app/clock_event` — Record a clock in/out event for the current student.  
  Body: `{"event_type": "clock_in"|"clock_out", "timestamp": "2025-01-01T15:00:00Z", "lat": 33.75, "lng": -84.39, "accuracy": 12.3}`  
  Response: `{"success": true, "event": {...}}` or `401/400/403`.

- `POST /app/clear-locations` — Student: delete only your own `StudentLocation` records and clear last-known location.  
  Response: `{"success": true, "message": "Cleared N location records"}` or `401`.

- `POST /app/clear-all-locations` — Professor: delete all *real* student locations (keeps demo data) and reset last-known positions.  
  Response: `{"success": true, "message": "..."}` or `401/500`.

- `POST /app/heartbeat` — Student presence ping; updates `last_seen`.  
  Response: `{"success": true}` or `401/404`.

- Notifications  
  - `GET /app/api/notifications?limit=20&unread_only=true|false` — Fetch inbox; returns `notifications`, `unread_count`.  
  - `POST /app/api/notifications/<id>/read` — Mark one as read.  
  - `DELETE|POST /app/api/notifications/<id>` — Delete one.  
  - `POST /app/api/notifications/mark-all-read` — Mark all read.  
  - `POST /app/api/notifications/preferences` — Update settings. Body example:  
    `{"browser_push_enabled": true, "location_alerts_enabled": true, "quiet_hours_start": "22:00", "quiet_hours_end": "07:00"}`  
  - `POST /app/api/notifications/push/subscribe` — Save a Web Push subscription. Body:  
    `{"subscription": {"endpoint": "...", "keys": {"p256dh": "...", "auth": "..."}}, "browser": "chrome", "device_type": "desktop"}`  
  - `POST /app/api/notifications/push/unsubscribe` — Remove one/all subscriptions. Body: `{"endpoint": "..."}` or `{}` for all.
  - `POST /app/api/notifications/test` — Create a test notification for the current user.
  - `POST /app/api/notifications/broadcast` — Professor: send a broadcast. Body: `{"title": "...", "message": "...", "target_type": "student"|"professor"|null}`.
  - `POST /app/api/notifications/cleanup` — Clean up expired/read/low-priority notifications. Body: `{"aggressive": true|false}`.
  - `POST /app/api/notifications/delete-all` — Delete all notifications for the current user.
  - `GET /app/api/notifications/stats` — Returns counts (total/unread/recent/expired).

- Classes (session required)  
  - `GET /app/classes/` — List classes (student: all + enrolled; professor: own).  
  - `POST /app/classes/<class_id>/enroll` — Student enroll.  
  - `POST /app/classes/<class_id>/drop` — Student drop.  
  - `POST /app/classes/<class_id>/toggle_enrollment` — Professor toggle open/closed.  
  - `POST /app/classes/<class_id>/edit` — Professor edit details; multipart form data.

## Project Layout
```
app.py                     # Entry point using the Flask factory
studenttracker/            # Application package
  __init__.py              # Factory, middleware, OAuth + DB setup, seed data
  models.py                # SQLAlchemy models (users, classes, locations, notifications)
  routes/                  # Auth, dashboards, API, notifications, classes, chat
  services/notification_service.py
  utils.py                 # Template filters, time-tracking helpers, geocoding
templates/                 # Jinja2 templates (auth, dashboards, classes, notifications)
static/                    # JS/CSS, map + notification assets
scripts/setup_database.py  # Local DB bootstrap helper
```

## Deployment Notes
- Set a strong `FLASK_SECRET`, enable HTTPS/secure cookies, and configure a proper reverse proxy (ProxyFix is pre-enabled).
- Use Alembic migrations for schema changes (`flask db migrate` / `flask db upgrade`).
- Replace the default Nominatim User-Agent with a contact email before production use.

## Contributors
- Jacob Hebert
- Deep Desai
- Shane Austin
- Ishwari Patel
