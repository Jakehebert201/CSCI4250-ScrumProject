"""Utilities for retrieving and persisting user location information."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


class LocationServiceError(RuntimeError):
    """Raised when the remote location service cannot be reached."""


@dataclass
class LocationRecord:
    """Represents a user's current location details."""

    latitude: float
    longitude: float
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "city": self.city,
            "region": self.region,
            "country": self.country,
        }


class LocationService:
    """Fetches user location data from an open API and stores it locally."""

    def __init__(
        self,
        data_directory: Path,
        *,
        api_url: str = "https://ipapi.co/json/",
        http_get: Optional[Callable[[str], Dict[str, object]]] = None,
    ) -> None:
        self.api_url = api_url
        self._data_directory = data_directory
        self._storage_path = data_directory / "user_locations.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._http_get = http_get or self._default_http_get
        if not self._storage_path.exists():
            self._persist({})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def record_location(self, user_id: str) -> LocationRecord:
        """Fetch the current location for ``user_id`` and persist it locally."""

        payload = self._http_get(self.api_url)
        record = self._build_record(payload)
        data = self._load_all()
        data[user_id] = record.to_dict()
        self._persist(data)
        return record

    def get_location(self, user_id: str) -> Optional[LocationRecord]:
        """Return the most recently stored location for the given user."""

        data = self._load_all()
        if user_id not in data:
            return None
        stored = data[user_id]
        return LocationRecord(
            latitude=float(stored["latitude"]),
            longitude=float(stored["longitude"]),
            city=stored.get("city"),
            region=stored.get("region"),
            country=stored.get("country"),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _default_http_get(self, url: str) -> Dict[str, object]:
        request = Request(url, headers={"User-Agent": "StudentTracker/1.0"})
        try:
            with urlopen(request, timeout=5) as response:
                raw = response.read().decode("utf-8")
        except URLError as exc:  # pragma: no cover - network issues
            raise LocationServiceError("Unable to contact location provider") from exc
        return json.loads(raw)

    def _build_record(self, payload: Dict[str, object]) -> LocationRecord:
        try:
            latitude = float(payload["latitude"])
            longitude = float(payload["longitude"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LocationServiceError("Location provider did not return coordinates") from exc

        city = payload.get("city") or payload.get("city_name")
        region = payload.get("region") or payload.get("region_name")
        country = payload.get("country_name") or payload.get("country")
        return LocationRecord(
            latitude=latitude,
            longitude=longitude,
            city=city if isinstance(city, str) else None,
            region=region if isinstance(region, str) else None,
            country=country if isinstance(country, str) else None,
        )

    def _load_all(self) -> Dict[str, Dict[str, object]]:
        with self._storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _persist(self, data: Dict[str, Dict[str, object]]) -> None:
        with self._storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
