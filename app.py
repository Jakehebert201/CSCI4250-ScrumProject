from __future__ import annotations

import ipaddress
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import urllib.request

from flask import Flask, jsonify, render_template, request


API_URL = "https://ipapi.co/{ip}/json/"


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        return render_template("index.html")

    @app.route("/api/location")
    def api_location() -> Any:
        requested_ip = _validated_ip(request.args.get("ip", "").strip())
        client_ip = _client_ip(request)

        ip_address: Optional[str] = client_ip
        if requested_ip:
            if client_ip and requested_ip != client_ip:
                return (
                    jsonify({"error": "The provided IP address does not match the client."}),
                    403,
                )
            if not client_ip:
                # If we cannot determine the client IP we ignore the parameter to avoid abuse.
                ip_address = None

        lookup_ip = ip_address or "json"
        data = _lookup_location(lookup_ip)
        if ip_address and data.get("ip") is None:
            data["ip"] = ip_address
        return jsonify(data)

    return app


@dataclass
class LocationResult:
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    postal: Optional[str]
    ip: Optional[str]

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "LocationResult":
        return cls(
            city=payload.get("city"),
            region=payload.get("region"),
            country=payload.get("country_name"),
            latitude=_safe_float(payload.get("latitude")),
            longitude=_safe_float(payload.get("longitude")),
            postal=payload.get("postal"),
            ip=payload.get("ip"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "city": self.city,
            "region": self.region,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "postal": self.postal,
            "ip": self.ip,
        }


def _lookup_location(ip: str) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(API_URL.format(ip=ip), timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return {"error": "Unable to determine location"}

    result = LocationResult.from_payload(payload)
    return result.to_dict()


def _client_ip(req: Any) -> Optional[str]:
    """Best-effort detection of the originating client IP address."""

    candidates: list[str] = []

    forwarded_for = req.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        candidates.extend(part.strip() for part in forwarded_for.split(",") if part.strip())

    forwarded_header = req.headers.get("Forwarded", "")
    if forwarded_header:
        candidates.extend(_parse_forwarded_header(forwarded_header))

    for header_name in ("CF-Connecting-IP", "True-Client-IP", "X-Real-IP"):
        header_value = req.headers.get(header_name, "").strip()
        if header_value:
            candidates.append(header_value)

    if getattr(req, "access_route", None):
        candidates.extend([str(item).strip() for item in req.access_route if str(item).strip()])

    if req.remote_addr:
        candidates.append(req.remote_addr.strip())

    cleaned_candidates = []
    for candidate in candidates:
        ip = _validated_ip(candidate)
        if ip:
            cleaned_candidates.append(ip)

    for ip in cleaned_candidates:
        if _is_public_ip(ip):
            return ip

    return cleaned_candidates[0] if cleaned_candidates else None


def _validated_ip(candidate: str) -> Optional[str]:
    candidate = candidate.strip()
    if not candidate or candidate.lower() == "unknown":
        return None

    if "%" in candidate:
        candidate = candidate.split("%", 1)[0]

    if candidate.startswith("\"") and candidate.endswith("\""):
        candidate = candidate[1:-1]

    if candidate.startswith("[") and "]" in candidate:
        closing_index = candidate.find("]")
        host = candidate[1:closing_index]
        remainder = candidate[closing_index + 1 :]
        if remainder.startswith(":") and remainder[1:].isdigit():
            candidate = host
        else:
            candidate = host + remainder

    if "." in candidate and candidate.count(":") == 1:
        host, possible_port = candidate.rsplit(":", 1)
        if possible_port.isdigit():
            candidate = host

    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None

    return candidate


def _is_public_ip(ip: str) -> bool:
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return False

    return not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_unspecified
        or parsed.is_reserved
        or parsed.is_multicast
    )


def _parse_forwarded_header(header_value: str) -> list[str]:
    candidates: list[str] = []
    for part in header_value.split(","):
        directives = [directive.strip() for directive in part.split(";") if directive.strip()]
        for directive in directives:
            if directive.lower().startswith("for="):
                value = directive[4:]
                if value.startswith("\"") and value.endswith("\""):
                    value = value[1:-1]
                candidates.append(value)
    return candidates


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
