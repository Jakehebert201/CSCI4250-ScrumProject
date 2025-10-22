from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import requests
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")

# OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get("GOOGLE_CLIENT_SECRET")

# SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studenttracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize OAuth only if credentials are provided
oauth = OAuth(app)
google = None

# Check if OAuth credentials are configured
oauth_enabled = bool(app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'))

if oauth_enabled:
    try:
        google = oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        print("✅ Google OAuth configured successfully")
    except Exception as e:
        print(f"❌ Failed to configure Google OAuth: {e}")
        oauth_enabled = False
else:
    print("⚠️  Google OAuth not configured - OAuth login disabled")

# Make oauth_enabled available to templates
app.jinja_env.globals['oauth_enabled'] = oauth_enabled


# ---------------------- MODELS ---------------------- #
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=True)  # University student ID (optional for OAuth)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Optional for OAuth users
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(20), nullable=True)  # Freshman, Sophomore, etc.
    last_lat = db.Column(db.Float, nullable=True)
    last_lng = db.Column(db.Float, nullable=True)
    last_accuracy = db.Column(db.Float, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    oauth_provider = db.Column(db.String(50), nullable=True)  # 'google', 'microsoft', etc.

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_oauth_user(self):
        return self.oauth_provider is not None


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=True)  # University employee ID (optional for OAuth)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Optional for OAuth users
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(100), nullable=True)  # Professor, Associate Professor, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    oauth_provider = db.Column(db.String(50), nullable=True)  # 'google', 'microsoft', etc.

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_oauth_user(self):
        return self.oauth_provider is not None


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), nullable=False)  # e.g., "CSCI 4250"
    course_name = db.Column(db.String(200), nullable=False)
    section = db.Column(db.String(10), nullable=True)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=False)
    semester = db.Column(db.String(20), nullable=False)  # e.g., "Fall 2025"
    year = db.Column(db.Integer, nullable=False)
    room = db.Column(db.String(50), nullable=True)
    schedule = db.Column(db.String(100), nullable=True)  # e.g., "MWF 10:00-11:00"
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    professor = db.relationship("Professor", backref=db.backref("classes", lazy="dynamic"))

    @property
    def full_course_name(self):
        return f"{self.course_code}: {self.course_name}"


class StudentLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    city = db.Column(db.String(255), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=True)  # Optional: which class they're attending
    notes = db.Column(db.Text, nullable=True)  # Optional notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", backref=db.backref("locations", lazy="dynamic"))
    class_attended = db.relationship("Class", backref=db.backref("student_locations", lazy="dynamic"))


# Keep the old User and Location models for backward compatibility during migration
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    last_lat = db.Column(db.Float, nullable=True)
    last_lng = db.Column(db.Float, nullable=True)
    last_accuracy = db.Column(db.Float, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    city = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("locations", lazy="dynamic"))


with app.app_context():
    db.create_all()


# ---------------------- UTILITIES ---------------------- #
def format_dt(dt):
    if not dt:
        return "-"
    s = dt.strftime("%b %d, %Y %I:%M %p")
    s = re.sub(r"\b0([0-9]):", r"\1:", s)
    s = s.replace("AM", "am").replace("PM", "pm")
    return s


app.jinja_env.filters["format_dt"] = format_dt


# ---------------------- ROUTES ---------------------- #
@app.route("/")
def landing_page():
    return render_template("index.html")


@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        major = request.form.get("major", "").strip()
        year = request.form.get("year", "").strip()

        if not all([student_id, username, password, email, first_name, last_name]):
            return render_template("register_student.html", error="All required fields must be filled")

        # Check for existing records
        if Student.query.filter_by(student_id=student_id).first():
            return render_template("register_student.html", error="Student ID already registered")
        if Student.query.filter_by(username=username).first():
            return render_template("register_student.html", error="Username already taken")
        if Student.query.filter_by(email=email).first():
            return render_template("register_student.html", error="Email already registered")

        student = Student(
            student_id=student_id,
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            first_name=first_name,
            last_name=last_name,
            major=major or None,
            year=year or None
        )
        db.session.add(student)
        db.session.commit()
        flash("Student account registered successfully. Please log in.")
        return redirect(url_for("login_student"))

    return render_template("register_student.html")


@app.route("/register/professor", methods=["GET", "POST"])
def register_professor():
    if request.method == "POST":
        employee_id = request.form.get("employee_id", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        department = request.form.get("department", "").strip()
        title = request.form.get("title", "").strip()

        if not all([employee_id, username, password, email, first_name, last_name]):
            return render_template("register_professor.html", error="All required fields must be filled")

        # Check for existing records
        if Professor.query.filter_by(employee_id=employee_id).first():
            return render_template("register_professor.html", error="Employee ID already registered")
        if Professor.query.filter_by(username=username).first():
            return render_template("register_professor.html", error="Username already taken")
        if Professor.query.filter_by(email=email).first():
            return render_template("register_professor.html", error="Email already registered")

        professor = Professor(
            employee_id=employee_id,
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            first_name=first_name,
            last_name=last_name,
            department=department or None,
            title=title or None
        )
        db.session.add(professor)
        db.session.commit()
        flash("Professor account registered successfully. Please log in.")
        return redirect(url_for("login_professor"))

    return render_template("register_professor.html")


@app.route("/login/student", methods=["GET", "POST"])
def login_student():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            return render_template("login_student.html", error="Username/email and password required")

        # Try to find student by username, email, or student_id
        student = Student.query.filter_by(username=identifier).first()
        if not student:
            student = Student.query.filter_by(email=identifier).first()
        if not student:
            student = Student.query.filter_by(student_id=identifier).first()

        if student and student.check_password(password):
            session["user_id"] = student.id
            session["user_type"] = "student"
            session["username"] = student.username
            session["full_name"] = student.full_name
            return redirect(url_for("student_dashboard"))

        return render_template("login_student.html", error="Invalid credentials")

    return render_template("login_student.html")


@app.route("/login/professor", methods=["GET", "POST"])
def login_professor():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            return render_template("login_professor.html", error="Username/email and password required")

        # Try to find professor by username, email, or employee_id
        professor = Professor.query.filter_by(username=identifier).first()
        if not professor:
            professor = Professor.query.filter_by(email=identifier).first()
        if not professor:
            professor = Professor.query.filter_by(employee_id=identifier).first()

        if professor and professor.check_password(password):
            session["user_id"] = professor.id
            session["user_type"] = "professor"
            session["username"] = professor.username
            session["full_name"] = professor.full_name
            return redirect(url_for("professor_dashboard"))

        return render_template("login_professor.html", error="Invalid credentials")

    return render_template("login_professor.html")


# OAuth Routes
@app.route("/oauth/login/<user_type>")
def oauth_login(user_type):
    if not oauth_enabled or not google:
        flash("OAuth is not configured. Please use traditional login or contact administrator.")
        return redirect(url_for('login'))
    
    if user_type not in ['student', 'professor']:
        flash("Invalid user type")
        return redirect(url_for('login'))
    
    try:
        # Store user type in session for callback
        session['oauth_user_type'] = user_type
        redirect_uri = url_for('oauth_callback', _external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        app.logger.error(f"OAuth login error: {e}")
        flash("OAuth login failed. Please try traditional login.")
        if user_type == 'student':
            return redirect(url_for('login_student'))
        else:
            return redirect(url_for('login_professor'))


@app.route("/oauth/callback")
def oauth_callback():
    if not oauth_enabled or not google:
        flash("OAuth is not configured.")
        return redirect(url_for('login'))
    
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            flash("Failed to get user information from Google")
            return redirect(url_for('login'))
        
        email = user_info.get('email')
        google_id = user_info.get('sub')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        profile_picture = user_info.get('picture')
        
        user_type = session.get('oauth_user_type', 'student')
        
        if user_type == 'student':
            # Check if student already exists
            student = Student.query.filter_by(email=email).first()
            if not student:
                student = Student.query.filter_by(google_id=google_id).first()
            
            if not student:
                # Create new student account
                student = Student(
                    email=email,
                    google_id=google_id,
                    first_name=first_name,
                    last_name=last_name,
                    profile_picture=profile_picture,
                    oauth_provider='google'
                )
                db.session.add(student)
                db.session.commit()
                flash("Welcome! Your student account has been created.")
            else:
                # Update existing student info
                student.google_id = google_id
                student.first_name = first_name
                student.last_name = last_name
                student.profile_picture = profile_picture
                student.oauth_provider = 'google'
                db.session.commit()
            
            # Log in the student
            session["user_id"] = student.id
            session["user_type"] = "student"
            session["username"] = student.email
            session["full_name"] = student.full_name
            session.pop('oauth_user_type', None)
            
            return redirect(url_for("student_dashboard"))
            
        else:  # professor
            # Check if professor already exists
            professor = Professor.query.filter_by(email=email).first()
            if not professor:
                professor = Professor.query.filter_by(google_id=google_id).first()
            
            if not professor:
                # Create new professor account
                professor = Professor(
                    email=email,
                    google_id=google_id,
                    first_name=first_name,
                    last_name=last_name,
                    profile_picture=profile_picture,
                    oauth_provider='google'
                )
                db.session.add(professor)
                db.session.commit()
                flash("Welcome! Your professor account has been created.")
            else:
                # Update existing professor info
                professor.google_id = google_id
                professor.first_name = first_name
                professor.last_name = last_name
                professor.profile_picture = profile_picture
                professor.oauth_provider = 'google'
                db.session.commit()
            
            # Log in the professor
            session["user_id"] = professor.id
            session["user_type"] = "professor"
            session["username"] = professor.email
            session["full_name"] = professor.full_name
            session.pop('oauth_user_type', None)
            
            return redirect(url_for("professor_dashboard"))
            
    except Exception as e:
        app.logger.error(f"OAuth callback error: {e}")
        flash("Authentication failed. Please try again.")
        return redirect(url_for('login'))


# Keep the old login route for backward compatibility
@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect to student login by default, or show a choice page
    return render_template("login_choice.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.")
    return redirect(url_for("landing_page"))


@app.route("/dashboard/student")
def student_dashboard():
    if not session.get("user_id") or session.get("user_type") != "student":
        return redirect(url_for("login_student"))

    student = Student.query.get(session.get("user_id"))
    if not student:
        session.clear()
        flash("Session invalid — please log in again.")
        return redirect(url_for("login_student"))

    return render_template(
        "student_dashboard.html",
        student=student,
        username=session.get("username"),
        full_name=session.get("full_name"),
        last_lat=student.last_lat,
        last_lng=student.last_lng,
        last_accuracy=student.last_accuracy,
        last_seen=student.last_seen,
    )


@app.route("/dashboard/professor")
def professor_dashboard():
    if not session.get("user_id") or session.get("user_type") != "professor":
        return redirect(url_for("login_professor"))

    professor = Professor.query.get(session.get("user_id"))
    if not professor:
        session.clear()
        flash("Session invalid — please log in again.")
        return redirect(url_for("login_professor"))

    # Get professor's classes and recent student locations
    classes = professor.classes.all()
    recent_locations = StudentLocation.query.order_by(StudentLocation.created_at.desc()).limit(50).all()

    return render_template(
        "professor_dashboard.html",
        professor=professor,
        username=session.get("username"),
        full_name=session.get("full_name"),
        classes=classes,
        recent_locations=recent_locations,
    )


# Keep the old dashboard route for backward compatibility
@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    user_type = session.get("user_type")
    if user_type == "student":
        return redirect(url_for("student_dashboard"))
    elif user_type == "professor":
        return redirect(url_for("professor_dashboard"))
    else:
        # Legacy user - redirect to choice page
        return redirect(url_for("login"))


@app.route("/update_location", methods=["POST"])
def update_location():
    if not session.get("user_id"):
        return jsonify({"error": "not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    try:
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
        acc = float(data.get("accuracy")) if data.get("accuracy") is not None else None
        class_id = data.get("class_id")  # Optional class ID
        notes = data.get("notes", "").strip()  # Optional notes
    except (TypeError, ValueError):
        return jsonify({"error": "invalid data"}), 400

    user_type = session.get("user_type")
    
    if user_type == "student":
        student = Student.query.get(session.get("user_id"))
        if not student:
            return jsonify({"error": "student not found"}), 404

        # Update student's last known location
        student.last_lat = lat
        student.last_lng = lng
        student.last_accuracy = acc
        student.last_seen = datetime.utcnow()

        # Reverse geocode to get city/town name
        city = get_city_from_coordinates(lat, lng)

        # Save the location in the StudentLocation table
        location = StudentLocation(
            student_id=student.id, 
            lat=lat, 
            lng=lng, 
            accuracy=acc, 
            city=city,
            class_id=int(class_id) if class_id and class_id.isdigit() else None,
            notes=notes or None
        )
        db.session.add(location)
        db.session.commit()

        return jsonify({"success": True, "city": city}), 200
    
    else:
        # Handle legacy users or professors (professors don't typically share location)
        user = User.query.get(session.get("user_id"))
        if not user:
            return jsonify({"error": "user not found"}), 404

        # Update user's last known location
        user.last_lat = lat
        user.last_lng = lng
        user.last_accuracy = acc
        user.last_seen = datetime.utcnow()

        city = get_city_from_coordinates(lat, lng)

        # Save the location in the old Location table for backward compatibility
        loc = Location(user_id=user.id, lat=lat, lng=lng, accuracy=acc, city=city)
        db.session.add(loc)
        db.session.commit()

        return jsonify({"success": True, "city": city}), 200


def get_city_from_coordinates(lat, lng):
    """Helper function to reverse geocode coordinates to city name"""
    try:
        headers = {"User-Agent": "StudentTracker/1.0 (contact@example.com)"}
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lng}&zoom=10&addressdetails=1"
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.ok:
            j = resp.json()
            addr = j.get("address", {}) if isinstance(j, dict) else {}

            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("municipality")
                or addr.get("hamlet")
                or addr.get("county")
                or addr.get("state")
                or "Unknown"
            )
            return city
    except Exception as e:
        app.logger.warning("Reverse geocode failed: %s", e)
    
    return "Unknown"


@app.route("/database")
def database():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    user_type = session.get("user_type")
    
    if user_type == "professor":
        # Professors can see all data
        students = Student.query.all()
        professors = Professor.query.all()
        classes = Class.query.all()
        student_locations = StudentLocation.query.order_by(StudentLocation.created_at.desc()).limit(100).all()
        
        return render_template("database.html", 
                             students=students, 
                             professors=professors,
                             classes=classes,
                             student_locations=student_locations,
                             user_type=user_type)
    
    elif user_type == "student":
        # Students can only see their own data
        student = Student.query.get(session.get("user_id"))
        student_locations = student.locations.order_by(StudentLocation.created_at.desc()).limit(50).all()
        
        return render_template("database.html", 
                             students=[student], 
                             student_locations=student_locations,
                             user_type=user_type)
    
    else:
        # Legacy users - show old data
        users = User.query.all()
        locations = Location.query.order_by(Location.created_at.desc()).limit(100).all()
        return render_template("database.html", users=users, locations=locations, user_type="legacy")


if __name__ == "__main__":
    app.run(debug=True)
