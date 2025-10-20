"""Entry point for running the student tracker as a small Flask web app."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional, Tuple

from flask import Flask, flash, redirect, render_template, request, url_for

from tracker import JSONDataStore, LocationService, ProfessorService, StudentService
from tracker.location_service import LocationServiceError
from tracker.student_service import StudentNotFoundError


def _default_data_path() -> Path:
    """Return the path to the bundled sample data file."""

    return Path(__file__).resolve().parent / "data" / "sample_data.json"


def create_app(data_path: Path | None = None) -> Flask:
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

        return render_template(
            "index.html",
            default_student_id=default_student_id,
            last_location=last_location,
        )

    def _client_ip() -> Optional[str]:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.remote_addr

    def _extract_coordinates(source: Mapping[str, object]) -> Optional[Tuple[float, float]]:
        latitude = source.get("latitude")
        longitude = source.get("longitude")
        if latitude is None or longitude is None:
            return None
        try:
            return float(latitude), float(longitude)
        except (TypeError, ValueError):
            return None

    @app.post("/api/location")
    def update_location():
        payload = request.get_json(silent=True) or {}
        student_id = (payload.get("student_id") or "").strip()
        if not student_id:
            return {"error": "Student ID is required"}, 400
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
