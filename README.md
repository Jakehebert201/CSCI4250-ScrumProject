# Student Location Tracker

A Flask web application that allows campus staff to monitor student check-ins. Authenticated users log in, grant browser geolocation access, and the app records their position with reverse geocoded city metadata for later review.

## Features
- Account registration and login backed by hashed passwords.
- Dashboard with a real-time Leaflet map and browser geolocation status.
- Location updates persisted to SQLite (`instance/studenttracker.db`) with reverse geocoding via OpenStreetMap’s Nominatim API.
- Admin-style database view that lists recent location updates and registered users.
- Clock in/out controls that persist attendance events and aggregate total time spent on campus per student per day.

## Tech Stack
- **Backend:** Flask, Flask-SQLAlchemy, Flask-Migrate
- **Frontend:** HTML templates (Jinja2), Leaflet.js, vanilla JavaScript, CSS
- **Database:** SQLite (default) with migration support via Alembic

## Getting Started
1. **Clone the project** and move into the repo directory.
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables (optional):**
   - `FLASK_SECRET`: Overrides the default development secret key.
5. **Initialize the database (first run only):**
   ```bash
   flask --app app db upgrade  # creates tables via Flask-Migrate
   ```
   or simply run:
   ```bash
   python scripts/setup_database.py
   ```
   The helper script will create the `migrations/` folder (if missing) and apply the latest schema. It targets the Flask app entry point at `tracker/app.py` (matching the Docker layout) and falls back to `app.py` when that path is absent; adjust `APP_FILE` inside the script if your structure differs. The application also calls `db.create_all()` on startup, so this step can be skipped for quick experiments, though migrations are recommended as the schema evolves.
6. **Run the application:**
   ```bash
   flask --app app run --debug
   ```
   or
   ```bash
   python app.py
   ```
7. **Open the app** at <http://127.0.0.1:5000>. Register a user, log in, and grant geolocation access on the dashboard page to start collecting location data.

## Project Structure
```
app.py                 # Flask application, models, routes
templates/             # Jinja2 templates (landing page, auth, dashboard, database view)
static/css/style.css   # Global styling
static/js/dashboard.js # Front-end geolocation + map logic
instance/studenttracker.db # SQLite database (created at runtime)
requirements.txt       # Python dependencies
```

## Key Routes
- `GET /` – Marketing landing page.
- `GET|POST /register/student` – Student account registration.
- `GET|POST /register/professor` – Professor account registration.
- `GET|POST /login/student` and `/login/professor` – Role-specific authentication.
- `GET /dashboard/student` – Student dashboard with real-time map, location status, and clock controls.
- `GET /dashboard/professor` – Professor dashboard with recent student activity.
- `POST /update_location` – Receives `{lat, lng, accuracy}` JSON payloads; updates user record and stores a location row.
- `POST /clock_event` – Accepts clock in/out events with optional coordinates.
- `GET /database` – Displays recent locations, registered users, and per-day campus time totals (requires login).

## Location & Time Tracking Workflow
1. User logs in and reaches the dashboard.
2. Browser geolocation retrieves the current position and updates the UI (`static/js/dashboard.js`).
3. The same geolocation payload is POSTed to `/update_location`.
4. Backend stores the coordinates, reverse geocodes the city name via Nominatim, and records the timestamp.
5. Users interact with the clock in/out buttons, which POST to `/clock_event`.
6. Backend persists each event and, on clock-out, calculates time elapsed since the prior clock-in, rolling totals into the `daily_campus_time` table (splitting multi-day spans automatically).
7. Admins and students can review time totals alongside location history in the `/database` view.

## Development Notes
- The default Nominatim request includes a simple User-Agent string; update it with contact details before production use.
- SQLite is stored under `instance/`. Add this directory to `.gitignore` (already practical) to avoid committing local databases.
- Consider enabling HTTPS and same-site cookie settings before deployment.
- When deploying behind nginx under `/app/`, the application automatically respects the prefix via `ProxyFix` + a custom middleware. The app defaults to `/app`; override with `APP_URL_PREFIX=/` (or forward `X-Script-Name`) if you want to develop at the site root.

## Future Enhancements
- Role-based access to separate student and staff dashboards.
- Automated migration workflow (`flask db migrate`) tied to a release process.
- Tests for authentication, location update API, and geocoding fallbacks.

## Contributors
- CSCI 4250 Scrum Team
