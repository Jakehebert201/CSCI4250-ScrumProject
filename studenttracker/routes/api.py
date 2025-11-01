from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session

from studenttracker.extensions import db
from studenttracker.models import ClockEvent, Location, Student, StudentLocation, User
from studenttracker.utils import add_daily_campus_time, get_city_from_coordinates, parse_event_timestamp

bp = Blueprint("api", __name__)


@bp.route("/update_location", methods=["POST"])
def update_location():
    if not session.get("user_id"):
        return jsonify({"error": "not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    try:
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
        acc = float(data.get("accuracy")) if data.get("accuracy") is not None else None
        class_id = data.get("class_id")
        notes = data.get("notes", "").strip()
    except (TypeError, ValueError):
        return jsonify({"error": "invalid data"}), 400

    user_type = session.get("user_type")

    if user_type == "student":
        student = Student.query.get(session.get("user_id"))
        if not student:
            return jsonify({"error": "student not found"}), 404

        student.last_lat = lat
        student.last_lng = lng
        student.last_accuracy = acc
        student.last_seen = datetime.utcnow()

        city = get_city_from_coordinates(lat, lng)

        location = StudentLocation(
            student_id=student.id,
            lat=lat,
            lng=lng,
            accuracy=acc,
            city=city,
            class_id=int(class_id) if class_id and str(class_id).isdigit() else None,
            notes=notes or None,
        )
        db.session.add(location)
        db.session.commit()

        return jsonify({"success": True, "city": city}), 200

    user = User.query.get(session.get("user_id"))
    if not user:
        return jsonify({"error": "user not found"}), 404

    user.last_lat = lat
    user.last_lng = lng
    user.last_accuracy = acc
    user.last_seen = datetime.utcnow()

    city = get_city_from_coordinates(lat, lng)

    loc = Location(user_id=user.id, lat=lat, lng=lng, accuracy=acc, city=city)
    db.session.add(loc)
    db.session.commit()

    return jsonify({"success": True, "city": city}), 200


@bp.route("/clock_event", methods=["POST"])
def clock_event():
    if not session.get("user_id"):
        return jsonify({"error": "not authenticated"}), 401

    if session.get("user_type") != "student":
        return jsonify({"error": "forbidden"}), 403

    student = Student.query.get(session.get("user_id"))
    if not student:
        return jsonify({"error": "student not found"}), 404

    data = request.get_json(silent=True) or request.form
    event_type = (data.get("event_type") or data.get("action") or "").strip().lower()

    if event_type in {"in", "clockin", "clock_in"}:
        event_type = "clock_in"
    elif event_type in {"out", "clockout", "clock_out"}:
        event_type = "clock_out"
    else:
        return jsonify({"error": "invalid event type"}), 400

    timestamp = parse_event_timestamp(data.get("timestamp") or data.get("recorded_at"))
    recorded_at = timestamp or datetime.utcnow()

    def _coerce_float(field):
        raw = data.get(field)
        if raw in (None, "", "null"):
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    lat = _coerce_float("lat")
    lng = _coerce_float("lng")
    accuracy = _coerce_float("accuracy")

    event = ClockEvent(
        student_id=student.id,
        event_type=event_type,
        recorded_at=recorded_at,
        lat=lat,
        lng=lng,
        accuracy=accuracy,
    )

    db.session.add(event)

    if event.event_type == "clock_out":
        clock_in_event = (
            ClockEvent.query.filter_by(student_id=student.id, event_type="clock_in")
            .filter(ClockEvent.recorded_at <= event.recorded_at)
            .order_by(ClockEvent.recorded_at.desc())
            .first()
        )
        if clock_in_event:
            has_intermediate_out = (
                ClockEvent.query.filter_by(student_id=student.id, event_type="clock_out")
                .filter(ClockEvent.recorded_at > clock_in_event.recorded_at, ClockEvent.recorded_at < event.recorded_at)
                .first()
            )
            if not has_intermediate_out:
                add_daily_campus_time(student.id, clock_in_event.recorded_at, event.recorded_at)

    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "event": {
                    "id": event.id,
                    "event_type": event.event_type,
                    "recorded_at": event.recorded_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                    "lat": event.lat,
                    "lng": event.lng,
                    "accuracy": event.accuracy,
                },
            }
        ),
        200,
    )
