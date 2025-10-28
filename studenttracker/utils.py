import re
from datetime import datetime, timedelta, timezone

import requests
from flask import current_app

from .extensions import db


def format_dt(dt):
    if not dt:
        return "-"
    formatted = dt.strftime("%b %d, %Y %I:%M %p")
    formatted = re.sub(r"\b0([0-9]):", r"\1:", formatted)
    return formatted.replace("AM", "am").replace("PM", "pm")


def format_duration(seconds):
    if seconds is None:
        return "--"
    try:
        total_seconds = int(seconds)
    except (TypeError, ValueError):
        return "--"
    if total_seconds < 0:
        total_seconds = 0
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


def register_template_filters(app):
    app.jinja_env.filters["format_dt"] = format_dt
    app.jinja_env.filters["format_duration"] = format_duration


def add_daily_campus_time(student_id, start_dt, end_dt):
    if not (student_id and start_dt and end_dt):
        return
    if end_dt <= start_dt:
        return

    from .models import DailyCampusTime

    current_start = start_dt
    while True:
        day = current_start.date()
        next_day_start = datetime.combine(day + timedelta(days=1), datetime.min.time())
        segment_end = min(end_dt, next_day_start)
        seconds = int((segment_end - current_start).total_seconds())
        if seconds > 0:
            daily_time = DailyCampusTime.query.filter_by(student_id=student_id, day=day).first()
            if not daily_time:
                daily_time = DailyCampusTime(student_id=student_id, day=day, total_seconds=0)
                db.session.add(daily_time)
            daily_time.total_seconds += seconds
        if segment_end >= end_dt:
            break
        current_start = segment_end


def parse_event_timestamp(raw_ts):
    if not raw_ts:
        return None
    value = raw_ts.strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def get_city_from_coordinates(lat, lng):
    """Reverse geocode coordinates to obtain a descriptive location."""
    try:
        headers = {"User-Agent": "StudentTracker/1.0 (contact@example.com)"}
        url = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?format=jsonv2&lat={lat}&lon={lng}&zoom=10&addressdetails=1"
        )
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.ok:
            payload = resp.json()
            if isinstance(payload, dict):
                addr = payload.get("address", {}) or {}
                city = (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or addr.get("municipality")
                    or addr.get("hamlet")
                    or addr.get("county")
                    or addr.get("state")
                )
                if city:
                    return city
    except Exception as exc:
        logger = getattr(current_app, "logger", None)
        if logger:
            logger.warning("Reverse geocode failed: %s", exc)
    return "Unknown"
