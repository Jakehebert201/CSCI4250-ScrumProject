"""Entry point for running the student tracker as a small Flask web app."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional, Tuple

from flask import Flask, render_template, request

from tracker import LocationService
from tracker.location_service import LocationServiceError


def _default_data_directory() -> Path:
    """Return the path to the application's bundled data directory."""

    return Path(__file__).resolve().parent / "data"


def _default_data_path() -> Path:
    """Backward-compatible alias for :func:`_default_data_directory`."""

    return _default_data_directory()


def create_app(
    data_directory: Path | None = None,
    *,
    data_path: Path | None = None,
) -> Flask:
    """Create the Flask application instance."""

    storage_root = data_directory or data_path or _default_data_directory()
    location_service = LocationService(storage_root)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev",
        LOCATION_SERVICE=location_service,
    )

    @app.route("/")
    def index():
        default_student_id = (request.args.get("student_id") or "").strip() or None
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

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
