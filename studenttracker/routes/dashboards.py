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


bp = Blueprint("main", __name__, template_folder="../../templates", static_folder="../../static")


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
    recent_locations = StudentLocation.query.order_by(StudentLocation.created_at.desc()).limit(50).all()

    return render_template(
        "professor_dashboard.html",
        professor=professor,
        username=session.get("username"),
        full_name=session.get("full_name"),
        classes=classes,
        recent_locations=recent_locations,
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
