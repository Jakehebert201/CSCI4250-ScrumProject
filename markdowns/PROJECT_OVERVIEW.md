# Student Location Tracker - Complete Project Overview

## 🎯 What This Project Does

**Student Location Tracker** is a Flask web application that helps professors monitor student attendance and location on campus in real-time. Students can check in with their GPS location, track their campus time, enroll in classes, and receive notifications. Professors can view live student locations on a map, manage classes, and send alerts.

---

## 🏗️ Architecture Overview

### **Tech Stack**
- **Backend**: Python Flask
- **Database**: SQLAlchemy ORM with SQLite / PostgreSQL
- **Frontend**: HTML, CSS, JavaScript (Vanilla JS + Leaflet.js for maps)
- **Authentication**: Password-based + Google OAuth 2.0
- **Security**: Flask-WTF, Flask-Limiter, Flask-Talisman

### **Project Structure**
```
app.py                          # Entry point
studenttracker/                 # Main application package
├── __init__.py                 # App factory, configuration
├── models.py                   # Database models
├── extensions.py               # Flask extensions (DB, OAuth, CSRF, etc.)
├── validators.py               # Input validation & sanitization
├── utils.py                    # Helper functions (geocoding, time tracking)
├── middleware.py               # Custom middleware (prefix handling)
├── routes/                     # Route blueprints
│   ├── auth.py                 # Login, registration, OAuth
│   ├── dashboards.py           # Student/professor dashboards
│   ├── api.py                  # REST API endpoints
│   ├── classes.py              # Class management
│   ├── notifications.py        # Notification system
│   └── chat.py                 # Chat features
└── services/
    └── notification_service.py # Notification logic
templates/                      # HTML templates (Jinja2)
static/                         # CSS, JavaScript, images
scripts/                        # Database setup scripts
```

---

## 🎨 Core Features (What You Built)

### **1. User Authentication System**
**What it does**: Secure login for students and professors

**Features**:
- Traditional username/password login
- Google OAuth 2.0 integration
- Separate registration for students and professors
- Profile completion after OAuth signup
- Session management with secure cookies
- "Impossible CAPTCHA" to encourage OAuth usage

**Files**:
- `studenttracker/routes/auth.py` - All auth logic
- `templates/login_*.html`, `register_*.html` - Login/registration pages

**How it works**:
1. User visits `/app/login/student` or `/app/login/professor`
2. Can login with username/password OR click "Sign in with Google"
3. OAuth redirects to Google, gets user info, creates/updates account
4. Session cookie stores user ID and type
5. Protected routes check session before allowing access

---

### **2. Real-Time Location Tracking**
**What it does**: Captures and displays student GPS locations on a map

**Features**:
- Browser geolocation API integration
- Live map with student markers (Leaflet.js)
- Reverse geocoding
- "Live" vs "All" toggle
- Location history tracking
- Accuracy indicators

**Files**:
- `studenttracker/routes/dashboards.py` - Dashboard routes
- `studenttracker/routes/api.py` - `/update_location` endpoint
- `studenttracker/utils.py` - Geocoding functions
- `templates/student_dashboard.html` - Student map view
- `templates/professor_dashboard.html` - Professor map view
- `static/js/` - Map JavaScript

**How it works**:
1. Student opens dashboard, browser asks for location permission
2. JavaScript gets GPS coordinates every 30 seconds
3. POST to `/app/update_location` with lat/lng/accuracy
4. Server reverse geocodes to get city name (Nominatim API)
5. Saves to `StudentLocation` table and updates `Student.last_lat/lng`
6. Professor dashboard fetches all locations, displays on map
7. "Live" filter shows only students active in last 5 minutes

---

### **3. Attendance Tracking (Clock In/Out)**
**What it does**: Students clock in/out to track time spent on campus

**Features**:
- Clock in/out buttons on student dashboard
- Automatic daily time calculation
- Prevents double clock-in or clock-out
- Location captured with each clock event
- Daily campus time totals

**Files**:
- `studenttracker/routes/api.py` - `/clock_event` endpoint
- `studenttracker/utils.py` - Time calculation functions
- `studenttracker/models.py` - `ClockEvent`, `DailyCampusTime` models

**How it works**:
1. Student clicks "Clock In" button
2. POST to `/app/clock_event` with `event_type: "clock_in"`
3. Creates `ClockEvent` record with timestamp and location
4. When clocking out, calculates time difference
5. Updates `DailyCampusTime` table with total seconds for that day
6. Dashboard displays formatted time (e.g., "2h 34m")

---

### **4. Class Management System**
**What it does**: Professors create classes, students enroll

**Features**:
- Create/edit/delete classes
- Class details (course code, name, section, schedule, room, capacity)
- Student enrollment with capacity limits
- Enrollment open/closed toggle
- Class roster view
- Student can browse and enroll in classes
- Drop class functionality

**Files**:
- `studenttracker/routes/classes.py` - All class routes
- `studenttracker/models.py` - `Class`, `student_class_enrollment` models
- `templates/classes/` - Class templates

**How it works**:
1. Professor creates class at `/app/classes/create`
2. Fills in course code, name, capacity, schedule, etc.
3. Saves to `Class` table
4. Students browse classes at `/app/classes/`
5. Click "Enroll" → checks capacity → adds to `student_class_enrollment` table
6. Many-to-many relationship: students can enroll in multiple classes

---

### **5. Notification System**
**What it does**: In-app notifications with preferences and push support

**Features**:
- In-app notification inbox
- Notification types (class reminders, attendance alerts, location alerts, emergency)
- User preferences (enable/disable channels, quiet hours)
- Browser push notification support
- Scheduled notifications
- Broadcast notifications
- Priority levels (low, normal, high, urgent)
- Action buttons on notifications
- Auto-cleanup of old notifications

**Files**:
- `studenttracker/routes/notifications.py` - Notification routes
- `studenttracker/services/notification_service.py` - Business logic
- `studenttracker/models.py` - `Notification`, `NotificationType`, `UserNotificationPreference`, `PushSubscription` models
- `templates/notifications/` - Notification UI

**How it works**:
1. System creates notification via `notification_service.create_notification()`
2. Saves to `Notification` table
3. If scheduled, waits until due time
4. When sending, checks user preferences (quiet hours, enabled channels)
5. Creates in-app notification (visible in inbox)
6. Optionally sends browser push notification
7. User can mark as read, delete, or dismiss
8. Cleanup job removes old/expired notifications

---

### **6. Database Management**
**What it does**: View and manage all data in the system

**Features**:
- View all students, professors, classes, locations
- Admin cleanup tools (clear locations, reset data)
- Preserves demo/fake data while clearing real data
- Database statistics

**Files**:
- `studenttracker/routes/dashboards.py` - `/database` route
- `templates/database.html` - Database view
- `templates/admin_cleanup.html` - Cleanup tools

**Models** (in `studenttracker/models.py`):
- `Student` - Student accounts
- `Professor` - Professor accounts
- `Class` - Course classes
- `StudentLocation` - GPS check-ins
- `ClockEvent` - Clock in/out events
- `DailyCampusTime` - Daily time totals
- `Notification` - Notifications
- `NotificationType` - Notification categories
- `UserNotificationPreference` - User settings
- `PushSubscription` - Browser push subscriptions

---

### **7. Security Features**
**What it does**: Protects against common web attacks

**Features**:
- CSRF protection on all forms
- Rate limiting on login/registration
- Input validation and sanitization
- Strong password requirements
- Secure session management
- Security headers (HSTS, CSP, X-Frame-Options)
- SQL injection protection (ORM)
- XSS prevention

**Files**:
- `studenttracker/validators.py` - Validation functions
- `studenttracker/extensions.py` - CSRF, rate limiter
- `studenttracker/__init__.py` - Security configuration

---

## 🔄 User Flows

### **Student Flow**:
1. Register or login → `/app/login/student`
2. Complete profile (if OAuth) → `/app/complete-profile/student`
3. View dashboard with map → `/app/dashboard/student`
4. Share location (automatic every 30s)
5. Clock in → `/app/clock_event`
6. Browse classes → `/app/classes/`
7. Enroll in class → `/app/classes/<id>/enroll`
8. Check notifications → `/app/notifications`
9. Clock out → `/app/clock_event`
10. Logout → `/app/logout`

### **Professor Flow**:
1. Register or login → `/app/login/professor`
2. View live student map → `/app/dashboard/professor`
3. Toggle "Live Only" to see active students
4. Create class → `/app/classes/create`
5. Manage class enrollment → `/app/classes/<id>/toggle_enrollment`
6. Send broadcast notification → `/app/api/notifications/broadcast`
7. View database → `/app/database`
8. Admin cleanup → `/app/notifications` (cleanup tools)

---

## 🛠️ Technical Implementation Details

### **1. Flask Application Factory Pattern**
- `studenttracker/__init__.py` contains `create_app()` function
- Initializes extensions (DB, OAuth, CSRF, etc.)
- Registers blueprints (routes)
- Creates seed data (sample users, classes)
- Configures middleware

### **2. Database with SQLAlchemy ORM**
- Models defined in `studenttracker/models.py`
- Relationships: Student ↔ Class (many-to-many), Professor → Class (one-to-many)
- Migrations with Flask-Migrate (Alembic)
- Automatic timestamps (`created_at`, `updated_at`)

### **3. OAuth 2.0 Integration**
- Uses Authlib library
- Configured in `__init__.py`
- Redirect URI: `/app/oauth/callback`
- Stores Google ID, profile picture
- Handles token exchange manually to avoid state issues

### **4. Geolocation & Mapping**
- Frontend: Browser Geolocation API
- Backend: Nominatim reverse geocoding (OpenStreetMap)
- Map library: Leaflet.js
- Markers show student names, last seen time, accuracy

### **5. Session Management**
- Flask sessions with secure cookies
- Stores: `user_id`, `user_type`, `username`, `full_name`
- HttpOnly, Secure (production), SameSite=Lax flags
- 24-hour timeout

### **6. API Endpoints**
All under `/app` prefix:
- `POST /update_location` - Save GPS location
- `POST /clock_event` - Clock in/out
- `POST /heartbeat` - Update last_seen
- `GET /api/notifications` - Get inbox
- `POST /api/notifications/broadcast` - Send to all
- `POST /classes/<id>/enroll` - Enroll in class
- Many more...

---

## 📊 Database Schema (Simplified)

```
Student
├── id, student_id, username, password_hash, email
├── first_name, last_name, major, year
├── last_lat, last_lng, last_accuracy, last_seen
├── google_id, profile_picture, oauth_provider
└── Relationships: enrolled_classes, locations, clock_events

Professor
├── id, employee_id, username, password_hash, email
├── first_name, last_name, department, title
├── google_id, profile_picture, oauth_provider
└── Relationships: classes

Class
├── id, course_code, course_name, section, professor_id
├── semester, year, room, schedule, capacity
├── meeting_days, start_time, end_time
├── is_active, enrollment_open
└── Relationships: professor, enrolled_students, student_locations

StudentLocation
├── id, student_id, lat, lng, accuracy, city
├── class_id, notes, created_at
└── Relationships: student, class_attended

ClockEvent
├── id, student_id, event_type (clock_in/clock_out)
├── recorded_at, lat, lng, accuracy
└── Relationships: student

DailyCampusTime
├── id, student_id, day, total_seconds
└── Relationships: student

Notification
├── id, user_id, user_type, title, message
├── priority, icon, action_url, is_read
├── scheduled_for, expires_at, created_at
└── Relationships: notification_type
```

---


### **Key Accomplishments to Highlight**:
1. **Full-stack development** - Backend (Flask/Python) + Frontend (HTML/CSS/JS)
2. **Real-time features** - Live location tracking, automatic updates
3. **OAuth integration** - Google single sign-on
4. **Geolocation** - GPS capture, reverse geocoding, map visualization
5. **Complex data relationships** - Many-to-many, one-to-many with SQLAlchemy
6. **Notification system** - Scheduled, prioritized, with push support
7. **Security hardening** - CSRF, rate limiting, input validation, secure sessions
8. **RESTful API** - JSON endpoints for location, notifications, classes
9. **User preferences** - Customizable notification settings, quiet hours
10. **Production-ready** - Environment configuration, migrations, documentation

---

## 📚 Technologies Used

**Backend**:
- Flask 3.1.2 (web framework)
- SQLAlchemy 2.0.44 (ORM)
- Flask-Migrate 4.1.0 (database migrations)
- Authlib 1.3.2 (OAuth)
- Flask-WTF 1.2.1 (CSRF protection)
- Flask-Limiter 3.5.0 (rate limiting)
- Flask-Talisman 1.1.0 (security headers)
- Bleach 6.1.0 (HTML sanitization)
- Email-Validator 2.1.0 (email validation)

**Frontend**:
- Leaflet.js (maps)
- Vanilla JavaScript (no frameworks)
- CSS3 (responsive design)
- HTML5 Geolocation API

**Database**:
- SQLite
- PostgreSQL

**APIs**:
- Google OAuth 2.0
- Nominatim (OpenStreetMap reverse geocoding)
- Web Push API (browser notifications)

