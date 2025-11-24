from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash
import requests

from studenttracker.extensions import db, oauth, limiter
from studenttracker.models import Professor, Student
from studenttracker.validators import (
    sanitize_input, validate_email_address, validate_password_strength,
    validate_username, validate_student_id, validate_employee_id, validate_name
)


def _get_google_client():
    try:
        return oauth.create_client("google") or getattr(oauth, "google", None)
    except Exception:
        return None


bp = Blueprint("auth", __name__)


@bp.route("/register/student", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register_student():
    if request.method == "POST":
        # Get and sanitize inputs
        student_id = sanitize_input(request.form.get("student_id", "").strip())
        username = sanitize_input(request.form.get("username", "").strip())
        password = request.form.get("password", "")
        email = sanitize_input(request.form.get("email", "").strip())
        first_name = sanitize_input(request.form.get("first_name", "").strip())
        last_name = sanitize_input(request.form.get("last_name", "").strip())
        major = sanitize_input(request.form.get("major", "").strip())
        year = sanitize_input(request.form.get("year", "").strip())

        # Validate required fields
        if not all([student_id, username, password, email, first_name, last_name]):
            return render_template("register_student.html", error="All required fields must be filled")

        # Validate student ID
        valid, error = validate_student_id(student_id)
        if not valid:
            return render_template("register_student.html", error=error)

        # Validate username
        valid, error = validate_username(username)
        if not valid:
            return render_template("register_student.html", error=error)

        # Validate password strength
        valid, error = validate_password_strength(password)
        if not valid:
            return render_template("register_student.html", error=error)

        # Validate email
        valid, error = validate_email_address(email)
        if not valid:
            return render_template("register_student.html", error=error)

        # Validate names
        valid, error = validate_name(first_name, "First name")
        if not valid:
            return render_template("register_student.html", error=error)

        valid, error = validate_name(last_name, "Last name")
        if not valid:
            return render_template("register_student.html", error=error)

        # Check for duplicates
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
@limiter.limit("10 per hour")
def register_professor():
    if request.method == "POST":
        # Get and sanitize inputs
        employee_id = sanitize_input(request.form.get("employee_id", "").strip())
        username = sanitize_input(request.form.get("username", "").strip())
        password = request.form.get("password", "")
        email = sanitize_input(request.form.get("email", "").strip())
        first_name = sanitize_input(request.form.get("first_name", "").strip())
        last_name = sanitize_input(request.form.get("last_name", "").strip())
        department = sanitize_input(request.form.get("department", "").strip())
        title = sanitize_input(request.form.get("title", "").strip())

        # Validate required fields
        if not all([employee_id, username, password, email, first_name, last_name]):
            return render_template("register_professor.html", error="All required fields must be filled")

        # Validate employee ID
        valid, error = validate_employee_id(employee_id)
        if not valid:
            return render_template("register_professor.html", error=error)

        # Validate username
        valid, error = validate_username(username)
        if not valid:
            return render_template("register_professor.html", error=error)

        # Validate password strength
        valid, error = validate_password_strength(password)
        if not valid:
            return render_template("register_professor.html", error=error)

        # Validate email
        valid, error = validate_email_address(email)
        if not valid:
            return render_template("register_professor.html", error=error)

        # Validate names
        valid, error = validate_name(first_name, "First name")
        if not valid:
            return render_template("register_professor.html", error=error)

        valid, error = validate_name(last_name, "Last name")
        if not valid:
            return render_template("register_professor.html", error=error)

        # Check for duplicates
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
@limiter.limit("5 per minute")
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
            session.pop("login_failed_student", None)  # Clear failed attempts on success
            return redirect(url_for("main.student_dashboard"))

        # Track failed login attempts
        failed_attempts = session.get("login_failed_student", 0) + 1
        session["login_failed_student"] = failed_attempts
        
        # Trigger CAPTCHA after first failed attempt
        show_captcha = failed_attempts >= 1
        
        return render_template("login_student.html", 
                             error="Invalid credentials", 
                             show_captcha=show_captcha,
                             oauth_url=url_for("auth.oauth_login", user_type="student"))

    # Don't show CAPTCHA on initial GET request
    return render_template("login_student.html", 
                         show_captcha=False,
                         oauth_url=url_for("auth.oauth_login", user_type="student"))


@bp.route("/login/professor", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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
            session.pop("login_failed_professor", None)  # Clear failed attempts on success
            return redirect(url_for("main.professor_dashboard"))

        # Track failed login attempts
        failed_attempts = session.get("login_failed_professor", 0) + 1
        session["login_failed_professor"] = failed_attempts
        
        # Trigger CAPTCHA after first failed attempt
        show_captcha = failed_attempts >= 1
        
        return render_template("login_professor.html", 
                             error="Invalid credentials", 
                             show_captcha=show_captcha,
                             oauth_url=url_for("auth.oauth_login", user_type="professor"))

    # Don't show CAPTCHA on initial GET request
    return render_template("login_professor.html", 
                         show_captcha=False,
                         oauth_url=url_for("auth.oauth_login", user_type="professor"))


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
        
        # Ensure consistent redirect URI format
        redirect_uri = redirect_uri.replace("127.0.0.1", "localhost")
        
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
        
        if 'access_token' not in token_json:
            raise Exception(f"Token exchange failed: {token_json}")
        
        # Get user info using the access token
        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f"Bearer {token_json['access_token']}"}
        )
        user_info = user_response.json()
        
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
            
            # Check if profile needs completion
            if not student.student_id or not student.username or not student.major or not student.year:
                return redirect(url_for("auth.complete_profile_student"))
            
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
        
        # Check if profile needs completion
        if not professor.employee_id or not professor.username or not professor.department or not professor.title:
            return redirect(url_for("auth.complete_profile_professor"))
        
        return redirect(url_for("main.professor_dashboard"))

    except Exception as exc:
        current_app.logger.error("OAuth callback error: %s", exc)
        flash("Authentication failed. Please try again.")
        return redirect(url_for("auth.login"))


@bp.route("/complete-profile/student", methods=["GET", "POST"])
def complete_profile_student():
    """Complete student profile after OAuth registration"""
    if not session.get("user_id") or session.get("user_type") != "student":
        return redirect(url_for("auth.login_student"))
    
    student = Student.query.get(session.get("user_id"))
    if not student:
        flash("Session invalid. Please log in again.")
        return redirect(url_for("auth.login_student"))
    
    # If profile is already complete, redirect to dashboard
    if student.student_id and student.username and student.major and student.year:
        return redirect(url_for("main.student_dashboard"))
    
    if request.method == "POST":
        try:
            student_id = request.form.get("student_id", "").strip()
            username = request.form.get("username", "").strip()
            major = request.form.get("major", "").strip()
            year = request.form.get("year", "").strip()
            
            if not all([student_id, username, major, year]):
                flash("Please fill in all required fields.")
                return render_template("complete_profile_student.html", student=student)
            
            # Check if student_id is already taken
            existing_student_id = Student.query.filter_by(student_id=student_id).first()
            if existing_student_id and existing_student_id.id != student.id:
                flash("Student ID already exists. Please choose a different one.")
                return render_template("complete_profile_student.html", student=student)
            
            # Check if username is already taken
            existing_username = Student.query.filter_by(username=username).first()
            if existing_username and existing_username.id != student.id:
                flash("Username already exists. Please choose a different one.")
                return render_template("complete_profile_student.html", student=student)
            
            # Update student profile
            student.student_id = student_id
            student.username = username
            student.major = major
            student.year = year
            db.session.commit()
            
            flash("Profile completed successfully! Welcome to Student Tracker.")
            return redirect(url_for("main.student_dashboard"))
            
        except Exception as e:
            db.session.rollback()
            flash("An error occurred. Please try again.")
            current_app.logger.error(f"Profile completion error: {e}")
    
    return render_template("complete_profile_student.html", student=student)


@bp.route("/complete-profile/professor", methods=["GET", "POST"])
def complete_profile_professor():
    """Complete professor profile after OAuth registration"""
    if not session.get("user_id") or session.get("user_type") != "professor":
        return redirect(url_for("auth.login_professor"))
    
    professor = Professor.query.get(session.get("user_id"))
    if not professor:
        flash("Session invalid. Please log in again.")
        return redirect(url_for("auth.login_professor"))
    
    # If profile is already complete, redirect to dashboard
    if professor.employee_id and professor.username and professor.department and professor.title:
        return redirect(url_for("main.professor_dashboard"))
    
    if request.method == "POST":
        try:
            employee_id = request.form.get("employee_id", "").strip()
            username = request.form.get("username", "").strip()
            department = request.form.get("department", "").strip()
            title = request.form.get("title", "").strip()
            
            if not all([employee_id, username, department, title]):
                flash("Please fill in all required fields.")
                return render_template("complete_profile_professor.html", professor=professor)
            
            # Check if employee_id is already taken
            existing_employee_id = Professor.query.filter_by(employee_id=employee_id).first()
            if existing_employee_id and existing_employee_id.id != professor.id:
                flash("Employee ID already exists. Please choose a different one.")
                return render_template("complete_profile_professor.html", professor=professor)
            
            # Check if username is already taken
            existing_username = Professor.query.filter_by(username=username).first()
            if existing_username and existing_username.id != professor.id:
                flash("Username already exists. Please choose a different one.")
                return render_template("complete_profile_professor.html", professor=professor)
            
            # Update professor profile
            professor.employee_id = employee_id
            professor.username = username
            professor.department = department
            professor.title = title
            db.session.commit()
            
            flash("Profile completed successfully! Welcome to Student Tracker.")
            return redirect(url_for("main.professor_dashboard"))
            
        except Exception as e:
            db.session.rollback()
            flash("An error occurred. Please try again.")
            current_app.logger.error(f"Profile completion error: {e}")
    
    return render_template("complete_profile_professor.html", professor=professor)


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
