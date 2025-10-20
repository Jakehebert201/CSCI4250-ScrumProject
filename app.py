"""Entry point for running the student tracker as a small Flask web app."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from flask import Flask, flash, redirect, render_template, request, url_for

from tracker import JSONDataStore, ProfessorService, StudentService
from tracker.student_service import (
    ActiveSessionExistsError,
    LocationValidationError,
    StudentNotFoundError,
    SessionNotFoundError,
)


def _default_data_path() -> Path:
    """Return the path to the bundled sample data file."""

    return Path(__file__).resolve().parent / "data" / "sample_data.json"


def _collect_highlights(student_service: StudentService, student_ids: Iterable[str]) -> List[Dict[str, str]]:
    """Generate a couple of friendly highlights for the landing page."""

    highlights: List[Dict[str, str]] = []
    for student_id in student_ids:
        gpa = student_service.calculate_gpa(student_id)
        if gpa is None:
            continue
        student = student_service.get_student(student_id)
        highlights.append(
            {
                "title": f"{student.name}'s GPA",
                "value": f"{gpa:.2f}",
            }
        )
        if len(highlights) == 2:
            break
    return highlights


def create_app(data_path: Path | None = None) -> Flask:
    """Create the Flask application instance."""

    datastore = JSONDataStore(data_path or _default_data_path())
    student_service = StudentService(datastore)
    professor_service = ProfessorService(datastore)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev",
        STUDENT_SERVICE=student_service,
        PROFESSOR_SERVICE=professor_service,
    )

    @app.route("/")
    def index():
        students = datastore.list_students()
        courses = datastore.list_courses()
        professors = datastore.list_professors()
        stats = {
            "Students": len(students),
            "Courses": len(courses),
            "Professors": len(professors),
        }
        highlights = _collect_highlights(student_service, (student.student_id for student in students))

        default_student_id = students[0].student_id if students else None
        sessions = (
            student_service.list_study_sessions(default_student_id)
            if default_student_id
            else []
        )
        active_session = student_service.datastore.get_active_study_session(default_student_id) if default_student_id else None
        notifications = (
            student_service.list_notifications(default_student_id)
            if default_student_id
            else []
        )

        return render_template(
            "index.html",
            stats=stats,
            students=students[:3],
            courses=courses[:3],
            highlights=highlights,
            default_student_id=default_student_id,
            sessions=sessions[:5],
            active_session=active_session,
            notifications=notifications[:5],
        )

    @app.route("/sprint-report")
    def sprint_report():
        return render_template("sprint_report.html")

    @app.post("/check-in")
    def check_in():
        student_id = request.form.get("student_id", "").strip()
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        if not student_id:
            flash("Student ID is required to check in", "error")
            return redirect(url_for("index"))
        try:
            lat_value = float(latitude)
            lon_value = float(longitude)
        except (TypeError, ValueError):
            flash("Latitude and longitude must be provided", "error")
            return redirect(url_for("index"))

        try:
            session = student_service.start_study_session(
                student_id, latitude=lat_value, longitude=lon_value
            )
        except StudentNotFoundError:
            flash("Unknown student ID", "error")
        except ActiveSessionExistsError:
            flash("You already have an active study session", "error")
        except LocationValidationError:
            flash("Please move within the campus geofence before checking in", "error")
        else:
            flash(
                f"Checked in at {session.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                "success",
            )
        return redirect(url_for("index"))

    @app.post("/check-out")
    def check_out():
        student_id = request.form.get("student_id", "").strip()
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        if not student_id:
            flash("Student ID is required to check out", "error")
            return redirect(url_for("index"))
        try:
            lat_value = float(latitude)
            lon_value = float(longitude)
        except (TypeError, ValueError):
            flash("Latitude and longitude must be provided", "error")
            return redirect(url_for("index"))

        try:
            session = student_service.end_study_session(
                student_id, latitude=lat_value, longitude=lon_value
            )
        except StudentNotFoundError:
            flash("Unknown student ID", "error")
        except SessionNotFoundError:
            flash("There is no active session to check out from", "error")
        except LocationValidationError:
            flash("Please move within the campus geofence before checking out", "error")
        else:
            if session.end_time and session.start_time:
                duration = session.end_time - session.start_time
                minutes = int(duration.total_seconds() // 60)
                seconds = int(duration.total_seconds() % 60)
                flash(
                    f"Session ended after {minutes}m {seconds}s of study time",
                    "success",
                )
            else:
                flash("Checked out successfully", "success")
        return redirect(url_for("index"))

    @app.route("/notifications", methods=["GET"])
    def notifications():
        students = datastore.list_students()
        default_student_id = students[0].student_id if students else None
        notifications_list = (
            student_service.list_notifications(default_student_id)
            if default_student_id
            else []
        )
        return render_template(
            "notifications.html",
            notifications=notifications_list,
            default_student_id=default_student_id,
        )

    @app.post("/notifications/send")
    def send_notification():
        professor_id = request.form.get("professor_id", "").strip()
        title = request.form.get("title", "")
        message = request.form.get("message", "")
        try:
            professor_service.send_notification(
                professor_id=professor_id, title=title, message=message
            )
        except LookupError:
            flash("Unknown professor ID", "error")
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Notification sent successfully", "success")
        return redirect(url_for("notifications"))

    @app.post("/notifications/<notification_id>/read")
    def mark_notification_read(notification_id: str):
        student_id = request.form.get("student_id", "").strip()
        if not student_id:
            flash("Student ID is required to mark notifications as read", "error")
            return redirect(url_for("notifications"))
        try:
            student_service.mark_notification_read(student_id, notification_id)
        except (StudentNotFoundError, LookupError):
            flash("Unable to mark notification as read", "error")
        else:
            flash("Notification marked as read", "success")
        return redirect(url_for("notifications"))

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
