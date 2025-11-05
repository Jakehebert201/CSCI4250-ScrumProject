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

@bp.route("/clear-locations", methods=["POST"])
def clear_student_locations():
    """Clear all locations for the current student"""
    if not session.get("user_id") or session.get("user_type") != "student":
        return jsonify({"error": "not authenticated as student"}), 401
    
    try:
        student_id = session.get("user_id")
        
        # Delete all StudentLocation records for this student
        deleted_count = StudentLocation.query.filter_by(student_id=student_id).delete()
        
        # Clear the student's last known location
        student = Student.query.get(student_id)
        if student:
            student.last_lat = None
            student.last_lng = None
            student.last_accuracy = None
            student.last_seen = None
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Cleared {deleted_count} location records"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/clear-all-locations", methods=["POST"])
def clear_all_locations():
    """Clear real student locations only (Professor only) - keeps fake demo data"""
    if not session.get("user_id") or session.get("user_type") != "professor":
        return jsonify({"error": "not authenticated as professor"}), 401
    
    try:
        # Delete only real StudentLocation records (not fake demo data)
        # Fake locations have notes starting with "International student from"
        real_locations = StudentLocation.query.filter(
            ~StudentLocation.notes.like('International student from%')
        ).all()
        
        deleted_count = 0
        for location in real_locations:
            db.session.delete(location)
            deleted_count += 1
        
        # Clear last known locations only for students who have real location data
        # Keep fake students' demo locations intact
        fake_student_emails = [
            "ahmad.hassan@university.edu",
            "dmitri.volkov@university.edu", 
            "emma.thompson@university.edu",
            "amara.okafor@university.edu",
            "hiroshi.tanaka@university.edu",
            "maria.santos@university.edu",
            "pierre.dubois@university.edu",
            "priya.sharma@university.edu",
            "carlos.rodriguez@university.edu",
            "fatima.alzahra@university.edu",
            "lars.andersen@university.edu",
            "chen.wei@university.edu",
            "sophia.mueller@university.edu",
            "kofi.asante@university.edu",
            "isabella.rossi@university.edu"
        ]
        
        # Clear locations for real students only
        real_students = Student.query.filter(~Student.email.in_(fake_student_emails)).all()
        for student in real_students:
            student.last_lat = None
            student.last_lng = None
            student.last_accuracy = None
            student.last_seen = None
        
        # Also clear legacy Location records if any exist (but keep fake ones)
        deleted_legacy = Location.query.delete()
        
        # Clear legacy User locations
        users = User.query.all()
        for user in users:
            user.last_lat = None
            user.last_lng = None
            user.last_accuracy = None
            user.last_seen = None
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Cleared {deleted_count} real student locations (kept demo data intact)"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    """Update student's last seen timestamp to track active sessions"""
    if not session.get("user_id") or session.get("user_type") != "student":
        return jsonify({"error": "not authenticated as student"}), 401
    
    try:
        student = Student.query.get(session.get("user_id"))
        if student:
            student.last_seen = datetime.utcnow()
            db.session.commit()
            return jsonify({"success": True})
        else:
            return jsonify({"error": "student not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500