from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash
import requests

from studenttracker.extensions import db, oauth
from studenttracker.models import Professor, Student


def _get_google_client():
    try:
        return oauth.create_client("google") or getattr(oauth, "google", None)
    except Exception:
        return None


bp = Blueprint("auth", __name__)


@bp.route("/register/student", methods=["GET", "POST"])
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
            year=year or None,
        )
        db.session.add(student)
        db.session.commit()
        flash("Student account registered successfully. Please log in.")
        return redirect(url_for("auth.login_student"))

    return render_template("register_student.html")


@bp.route("/register/professor", methods=["GET", "POST"])
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
            title=title or None,
        )
        db.session.add(professor)
        db.session.commit()
        flash("Professor account registered successfully. Please log in.")
        return redirect(url_for("auth.login_professor"))

    return render_template("register_professor.html")


@bp.route("/login/student", methods=["GET", "POST"])
def login_student():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            return render_template("login_student.html", error="Username/email and password required")

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
            return redirect(url_for("main.student_dashboard"))

        return render_template("login_student.html", error="Invalid credentials")

    return render_template("login_student.html")


@bp.route("/login/professor", methods=["GET", "POST"])
def login_professor():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            return render_template("login_professor.html", error="Username/email and password required")

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
            return redirect(url_for("main.professor_dashboard"))

        return render_template("login_professor.html", error="Invalid credentials")

    return render_template("login_professor.html")


@bp.route("/oauth/login/<user_type>")
def oauth_login(user_type):
    if not current_app.config.get("OAUTH_ENABLED"):
        flash("OAuth is not configured. Please use traditional login or contact administrator.")
        return redirect(url_for("auth.login"))

    if user_type not in {"student", "professor"}:
        flash("Invalid user type")
        return redirect(url_for("auth.login"))

    google_client = _get_google_client()
    if not google_client:
        flash("OAuth is unavailable. Please try again later.")
        return redirect(url_for("auth.login"))

    try:
        session["oauth_user_type"] = user_type
        redirect_uri = url_for("auth.oauth_callback", _external=True)
        current_app.logger.info(f"Generated redirect URI: {redirect_uri}")
        
        # Ensure consistent redirect URI format
        redirect_uri = redirect_uri.replace("127.0.0.1", "localhost")
        current_app.logger.info(f"Final redirect URI: {redirect_uri}")
        
        return google_client.authorize_redirect(redirect_uri)
    except Exception as exc:
        current_app.logger.error("OAuth login error: %s", exc)
        flash("OAuth login failed. Please try traditional login.")
        target_endpoint = "auth.login_student" if user_type == "student" else "auth.login_professor"
        return redirect(url_for(target_endpoint))


@bp.route("/oauth/callback")
def oauth_callback():
    if not current_app.config.get("OAUTH_ENABLED"):
        flash("OAuth is not configured.")
        return redirect(url_for("auth.login"))

    google_client = _get_google_client()
    if not google_client:
        flash("OAuth is unavailable. Please try again later.")
        return redirect(url_for("auth.login"))

    try:
        # Debug the callback request
        current_app.logger.info(f"Callback request args: {request.args}")
        current_app.logger.info(f"Session keys: {list(session.keys())}")
        
        # Handle the OAuth callback with manual token exchange to avoid state issues
        auth_code = request.args.get('code')
        if not auth_code:
            raise Exception("No authorization code received")
        
        # Exchange the code for tokens manually
        token_data = {
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('auth.oauth_callback', _external=True)
        }
        
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_json = token_response.json()
        current_app.logger.info(f"Token response: {token_json}")
        
        if 'access_token' not in token_json:
            raise Exception(f"Token exchange failed: {token_json}")
        
        # Get user info using the access token
        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f"Bearer {token_json['access_token']}"}
        )
        user_info = user_response.json()
        current_app.logger.info(f"User info: {user_info}")
        
        if not user_info or 'email' not in user_info:
            flash("Failed to get user information from Google")
            return redirect(url_for("auth.login"))

        email = user_info.get("email")
        google_id = user_info.get("id")  # Google API v2 uses 'id' instead of 'sub'
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")
        profile_picture = user_info.get("picture")
        
        # Since session might be empty, we'll default to student but allow override
        user_type = session.get("oauth_user_type", "student")
        current_app.logger.info(f"Processing OAuth for user_type: {user_type}, email: {email}")

        if user_type == "student":
            student = Student.query.filter_by(email=email).first() or Student.query.filter_by(google_id=google_id).first()
            if not student:
                student = Student(
                    email=email,
                    google_id=google_id,
                    first_name=first_name,
                    last_name=last_name,
                    profile_picture=profile_picture,
                    oauth_provider="google",
                )
                db.session.add(student)
                db.session.commit()
                flash("Welcome! Your student account has been created.")
            else:
                student.google_id = google_id
                student.first_name = first_name
                student.last_name = last_name
                student.profile_picture = profile_picture
                student.oauth_provider = "google"
                db.session.commit()

            session["user_id"] = student.id
            session["user_type"] = "student"
            session["username"] = student.email
            session["full_name"] = student.full_name
            session.pop("oauth_user_type", None)
            return redirect(url_for("main.student_dashboard"))

        professor = Professor.query.filter_by(email=email).first() or Professor.query.filter_by(google_id=google_id).first()
        if not professor:
            professor = Professor(
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
                oauth_provider="google",
            )
            db.session.add(professor)
            db.session.commit()
            flash("Welcome! Your professor account has been created.")
        else:
            professor.google_id = google_id
            professor.first_name = first_name
            professor.last_name = last_name
            professor.profile_picture = profile_picture
            professor.oauth_provider = "google"
            db.session.commit()

        session["user_id"] = professor.id
        session["user_type"] = "professor"
        session["username"] = professor.email
        session["full_name"] = professor.full_name
        session.pop("oauth_user_type", None)
        return redirect(url_for("main.professor_dashboard"))

    except Exception as exc:
        current_app.logger.error("OAuth callback error: %s", exc)
        flash("Authentication failed. Please try again.")
        return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login_choice.html")


@bp.route("/oauth/test")
def oauth_test():
    """Test route to check OAuth configuration"""
    oauth_enabled = current_app.config.get("OAUTH_ENABLED")
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
    jinja_oauth = current_app.jinja_env.globals.get("oauth_enabled")
    
    return f"""
    <h1>OAuth Configuration Test</h1>
    <p><strong>OAUTH_ENABLED (config):</strong> {oauth_enabled}</p>
    <p><strong>oauth_enabled (jinja):</strong> {jinja_oauth}</p>
    <p><strong>GOOGLE_CLIENT_ID:</strong> {client_id[:20] if client_id else 'None'}...</p>
    <p><strong>GOOGLE_CLIENT_SECRET:</strong> {'Set' if client_secret else 'Not Set'}</p>
    <hr>
    <p><a href="{url_for('auth.login')}">Back to Login</a></p>
    """

@bp.route("/logout")
def logout():
    # Mark student as inactive if they're logging out
    if session.get("user_type") == "student" and session.get("user_id"):
        try:
            from studenttracker.models import Student
            from studenttracker.extensions import db
            from datetime import datetime, timedelta
            
            student = Student.query.get(session.get("user_id"))
            if student:
                # Set last_seen to 5 minutes ago to ensure they don't appear as "live"
                student.last_seen = datetime.utcnow() - timedelta(minutes=5)
                db.session.commit()
        except Exception as e:
            # Don't fail logout if there's an error updating student status
            pass
    
    session.clear()
    flash("You have been logged out successfully.")
    return redirect(url_for("main.landing_page"))
