"""Entry point for running the student tracker as a small Flask web app."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional, Tuple

from flask import Flask, render_template, request

from tracker import JSONDataStore, LocationService, ProfessorService, StudentService
from tracker.location_service import LocationServiceError
from tracker.student_service import (
    ActiveSessionExistsError,
    LocationValidationError,
    StudentNotFoundError,
    SessionNotFoundError,
)


def _default_data_directory() -> Path:
    """Return the path to the application's bundled data directory."""

    return Path(__file__).resolve().parent / "data"


def create_app(
    data_directory: Path | None = None,
    *,
    data_path: Path | None = None,
) -> Flask:
    """Create the Flask application instance."""

    data_file = data_path or _default_data_path()
    datastore = JSONDataStore(data_file)
    student_service = StudentService(datastore)
    professor_service = ProfessorService(datastore)
    location_service = LocationService(data_file.parent)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev",
        STUDENT_SERVICE=student_service,
        PROFESSOR_SERVICE=professor_service,
        LOCATION_SERVICE=location_service,
    )

    @app.route("/")
    def index():
        students = datastore.list_students()
        default_student_id = students[0].student_id if students else None
        last_location = (
            location_service.get_location(default_student_id)
            if default_student_id
            else None
        )
        last_location = (
            location_service.get_location(default_student_id)
            if default_student_id
            else None
        )

        return render_template(
            "index.html",
            default_student_id=default_student_id,
            sessions=sessions[:5],
            active_session=active_session,
            notifications=notifications[:5],
            last_location=last_location,
        )

    @app.post("/check-in")
    def check_in():
        student_id = request.form.get("student_id", "").strip()
        if not student_id:
            flash("Student ID is required to check in", "error")
            return redirect(url_for("index"))
        try:
            location = location_service.record_location(student_id)
        except LocationServiceError:
            flash("Unable to determine your current location. Please try again.", "error")
            return redirect(url_for("index"))
        try:
            session = student_service.start_study_session(
                student_id, latitude=location.latitude, longitude=location.longitude
            )
        except StudentNotFoundError:
            flash("Unknown student ID", "error")
        except ActiveSessionExistsError:
            flash("You already have an active study session", "error")
        except LocationValidationError:
            flash("Please move within the campus geofence before checking in", "error")
        else:
            message = (
                f"Checked in at {session.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            if location.city or location.country:
                location_label = ", ".join(
                    part for part in (location.city, location.region, location.country) if part
                )
                message += f" from {location_label}"
            flash(message, "success")
        return redirect(url_for("index"))

    @app.post("/check-out")
    def check_out():
        student_id = request.form.get("student_id", "").strip()
        if not student_id:
            return {"error": "Student ID is required"}, 400
        try:
            location = location_service.record_location(student_id)
        except LocationServiceError:
            flash("Unable to determine your current location. Please try again.", "error")
            return redirect(url_for("index"))
        try:
            session = student_service.end_study_session(
                student_id, latitude=location.latitude, longitude=location.longitude
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
                message = f"Session ended after {minutes}m {seconds}s of study time"
                if location.city or location.country:
                    location_label = ", ".join(
                        part for part in (location.city, location.region, location.country) if part
                    )
                    message += f" near {location_label}"
                flash(message, "success")
            else:
                flash("Checked out successfully", "success")
        return redirect(url_for("index"))

    @app.post("/api/location")
    def update_location():
        payload = request.get_json(silent=True) or {}
        student_id = (payload.get("student_id") or "").strip()
        if not student_id:
            return {"error": "Student ID is required"}, 400
        try:
            record = location_service.record_location(student_id)
        except LocationServiceError:
            return {"error": "Unable to determine your current location."}, 503
        return {
            "latitude": record.latitude,
            "longitude": record.longitude,
            "city": record.city,
            "region": record.region,
            "country": record.country,
        }

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
            record = location_service.record_location(
                student_id,
                ip_address=_client_ip(),
                coordinates=_extract_coordinates(payload),
            )
        except LocationServiceError:
            return {"error": "Unable to determine your current location."}, 503
        return {
            "latitude": record.latitude,
            "longitude": record.longitude,
            "city": record.city,
            "region": record.region,
            "country": record.country,
        }

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
