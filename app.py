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
        requested_ip = request.args.get("ip", "").strip()
        ip_address = _validated_ip(requested_ip) or _client_ip(request)
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
    header = req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    candidate = header or req.remote_addr or ""
    return _validated_ip(candidate)


def _validated_ip(candidate: str) -> Optional[str]:
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
