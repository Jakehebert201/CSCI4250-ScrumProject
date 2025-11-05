from flask import Blueprint, flash, redirect, render_template, session, url_for

from studenttracker.models import (
    Class,
    DailyCampusTime,
    Location,
    Professor,
    Student,
    StudentLocation,
    User,
)


bp = Blueprint("main", __name__)


@bp.route("/")
def landing_page():
    return render_template("index.html")


@bp.route("/start")
def login():
    return redirect(url_for("auth.login"))


@bp.route("/dashboard/student")
def student_dashboard():
    if not session.get("user_id") or session.get("user_type") != "student":
        return redirect(url_for("auth.login_student"))

    student = Student.query.get(session.get("user_id"))
    if not student:
        session.clear()
        flash("Session invalid — please log in again.")
        return redirect(url_for("auth.login_student"))

    # Get student's recent locations
    student_locations = StudentLocation.query.filter_by(student_id=student.id).order_by(StudentLocation.created_at.desc()).limit(20).all()

    return render_template(
        "student_dashboard.html",
        student=student,
        student_locations=student_locations,
        username=session.get("username"),
        full_name=session.get("full_name"),
        last_lat=student.last_lat,
        last_lng=student.last_lng,
        last_accuracy=student.last_accuracy,
        last_seen=student.last_seen,
    )


@bp.route("/dashboard/professor")
def professor_dashboard():
    if not session.get("user_id") or session.get("user_type") != "professor":
        return redirect(url_for("auth.login_professor"))

    professor = Professor.query.get(session.get("user_id"))
    if not professor:
        session.clear()
        flash("Session invalid — please log in again.")
        return redirect(url_for("auth.login_professor"))

    classes = professor.classes.all()
    from datetime import datetime, timedelta
    
    # Get all locations, but prioritize recent ones
    recent_locations_query = StudentLocation.query.order_by(StudentLocation.created_at.desc()).limit(100).all()
    
    # Serialize location data for JavaScript
    recent_locations = []
    now = datetime.utcnow()
    
    for location in recent_locations_query:
        # Check if this is a fake student location
        is_fake = location.notes and location.notes.startswith('International student from')
        
        # Calculate if this location is "live" based on student's last_seen (heartbeat)
        # Use student's last_seen if available, otherwise fall back to location timestamp
        if is_fake:
            is_live = False
        else:
            # Check student's last heartbeat (last_seen) - live if within 3 minutes
            if location.student.last_seen:
                time_diff = now - location.student.last_seen
                is_live = time_diff.total_seconds() < 180  # 3 minutes (heartbeat is every 2 minutes)
            else:
                # Fallback to location timestamp if no last_seen
                time_diff = now - location.created_at
                is_live = time_diff.total_seconds() < 180  # 3 minutes
        
        recent_locations.append({
            'lat': location.lat,
            'lng': location.lng,
            'city': location.city,
            'created_at': location.created_at.isoformat(),
            'is_live': is_live,
            'is_fake': is_fake,
            'student': {
                'full_name': location.student.full_name
            }
        })

    return render_template(
        "professor_dashboard.html",
        professor=professor,
        username=session.get("username"),
        full_name=session.get("full_name"),
        classes=classes,
        recent_locations=recent_locations,
        recent_locations_raw=recent_locations_query,  # For the activity list
    )


@bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_type = session.get("user_type")
    if user_type == "student":
        return redirect(url_for("main.student_dashboard"))
    if user_type == "professor":
        return redirect(url_for("main.professor_dashboard"))
    return redirect(url_for("auth.login"))


@bp.route("/database")
def database():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_type = session.get("user_type")

    if user_type == "professor":
        students = Student.query.all()
        professors = Professor.query.all()
        classes = Class.query.all()
        student_locations = StudentLocation.query.order_by(StudentLocation.created_at.desc()).limit(100).all()
        daily_times = DailyCampusTime.query.order_by(DailyCampusTime.day.desc(), DailyCampusTime.student_id).limit(200).all()

        return render_template(
            "database.html",
            students=students,
            professors=professors,
            classes=classes,
            student_locations=student_locations,
            daily_times=daily_times,
            user_type=user_type,
        )

    if user_type == "student":
        student = Student.query.get(session.get("user_id"))
        if not student:
            session.clear()
            flash("Session invalid — please log in again.")
            return redirect(url_for("auth.login_student"))
        student_locations = student.locations.order_by(StudentLocation.created_at.desc()).limit(50).all()
        daily_times = student.daily_campus_times.order_by(DailyCampusTime.day.desc()).all()

        return render_template(
            "database.html",
            students=[student],
            student_locations=student_locations,
            daily_times=daily_times,
            user_type=user_type,
        )

    users = User.query.all()
    locations = Location.query.order_by(Location.created_at.desc()).limit(100).all()
    return render_template("database.html", users=users, locations=locations, daily_times=[], user_type="legacy")
