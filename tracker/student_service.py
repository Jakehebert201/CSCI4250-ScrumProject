"""Student-facing services for the student tracker application."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from .datastore import JSONDataStore
from .models import Course, Enrollment, Notification, Student, StudySession


class StudentNotFoundError(LookupError):
    """Raised when a student cannot be located in the data store."""


class ActiveSessionExistsError(RuntimeError):
    """Raised when a student attempts to start a session while one is active."""


class SessionNotFoundError(LookupError):
    """Raised when a student attempts to modify a session that is not active."""


class LocationValidationError(ValueError):
    """Raised when a student's reported location falls outside the approved area."""


class StudentService:
    """Provides access to student-oriented grade and GPA views."""

    def __init__(self, datastore: JSONDataStore):
        self.datastore = datastore
        # Downtown campus coordinates (Atlanta, GA) used as default study hub.
        self._campus_latitude = 33.7550
        self._campus_longitude = -84.3900
        self._campus_radius_meters = 150.0

    # ------------------------------------------------------------------
    # Retrieval helpers
    # ------------------------------------------------------------------
    def get_student(self, student_id: str) -> Student:
        student = self.datastore.get_student(student_id)
        if not student:
            raise StudentNotFoundError(f"Student '{student_id}' not found")
        return student

    def list_semesters(self, student_id: str) -> List[str]:
        self.get_student(student_id)
        semesters = {
            self._course_lookup(enrollment.course_id).semester
            for enrollment in self._student_enrollments(student_id)
        }
        return sorted(semesters)

    def get_grades_by_semester(self, student_id: str, semester: str) -> List[Dict[str, object]]:
        self.get_student(student_id)
        records = []
        for enrollment in self._student_enrollments(student_id):
            course = self._course_lookup(enrollment.course_id)
            if course.semester != semester:
                continue
            records.append({
                "course_id": course.course_id,
                "course_name": course.name,
                "credits": course.credits,
                "grade": enrollment.grade,
            })
        return records

    def get_all_grades(self, student_id: str) -> Dict[str, List[Dict[str, object]]]:
        grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        for enrollment in self._student_enrollments(student_id):
            course = self._course_lookup(enrollment.course_id)
            grouped[course.semester].append({
                "course_id": course.course_id,
                "course_name": course.name,
                "credits": course.credits,
                "grade": enrollment.grade,
            })
        return dict(sorted(grouped.items()))

    def calculate_gpa(self, student_id: str, semester: Optional[str] = None) -> Optional[float]:
        """Calculate the GPA for the requested student.

        Args:
            student_id: The identifier of the student.
            semester: If provided, limits the calculation to the given semester.

        Returns:
            The GPA rounded to two decimal places, or ``None`` if there are no
            graded credits for the requested scope.
        """

        self.get_student(student_id)
        total_points = 0.0
        total_credits = 0.0
        for enrollment in self._student_enrollments(student_id):
            if enrollment.grade is None:
                continue
            course = self._course_lookup(enrollment.course_id)
            if semester and course.semester != semester:
                continue
            total_points += enrollment.grade * course.credits
            total_credits += course.credits

        if total_credits == 0:
            return None
        return round(total_points / total_credits, 2)

    def filter_courses(
        self,
        student_id: str,
        *,
        semester: Optional[str] = None,
        course_name: Optional[str] = None,
        min_grade: Optional[float] = None,
        max_grade: Optional[float] = None,
    ) -> List[Dict[str, object]]:
        """Filter the student's courses according to the provided parameters."""

        self.get_student(student_id)
        matches: List[Dict[str, object]] = []
        for enrollment in self._student_enrollments(student_id):
            course = self._course_lookup(enrollment.course_id)
            if semester and course.semester != semester:
                continue
            if course_name and course_name.lower() not in course.name.lower():
                continue
            if min_grade is not None and (enrollment.grade is None or enrollment.grade < min_grade):
                continue
            if max_grade is not None and (enrollment.grade is None or enrollment.grade > max_grade):
                continue
            matches.append({
                "course_id": course.course_id,
                "course_name": course.name,
                "semester": course.semester,
                "credits": course.credits,
                "grade": enrollment.grade,
            })
        return matches

    # ------------------------------------------------------------------
    # Study session management
    # ------------------------------------------------------------------
    def start_study_session(self, student_id: str, *, latitude: float, longitude: float) -> StudySession:
        """Start a new study session for the given student with geofence validation."""

        self.get_student(student_id)
        if self.datastore.get_active_study_session(student_id):
            raise ActiveSessionExistsError("An active study session already exists")

        if not self._within_campus(latitude, longitude):
            raise LocationValidationError("Student must be within the designated study area to check in")

        session = StudySession(
            session_id=str(uuid4()),
            student_id=student_id,
            start_time=datetime.utcnow(),
            start_latitude=latitude,
            start_longitude=longitude,
        )
        self.datastore.upsert_study_session(session)
        return session

    def end_study_session(self, student_id: str, *, latitude: float, longitude: float) -> StudySession:
        """End the currently active study session for a student."""

        self.get_student(student_id)
        session = self.datastore.get_active_study_session(student_id)
        if not session:
            raise SessionNotFoundError("No active study session found")

        if not self._within_campus(latitude, longitude):
            raise LocationValidationError("Student must be within the designated study area to check out")

        session.end_time = datetime.utcnow()
        session.end_latitude = latitude
        session.end_longitude = longitude
        self.datastore.upsert_study_session(session)
        return session

    def list_study_sessions(self, student_id: str) -> List[StudySession]:
        self.get_student(student_id)
        sessions = [
            session
            for session in self.datastore.list_study_sessions()
            if session.student_id == student_id
        ]
        return sorted(sessions, key=lambda session: session.start_time, reverse=True)

    # ------------------------------------------------------------------
    # Notification utilities
    # ------------------------------------------------------------------
    def list_notifications(self, student_id: str) -> List[Notification]:
        self.get_student(student_id)
        notifications = self.datastore.list_notifications()
        return sorted(notifications, key=lambda item: item.sent_at, reverse=True)

    def mark_notification_read(self, student_id: str, notification_id: str) -> Notification:
        self.get_student(student_id)
        notification = self.datastore.get_notification(notification_id)
        if not notification:
            raise LookupError(f"Notification '{notification_id}' not found")
        if student_id not in notification.read_by:
            notification.read_by.append(student_id)
            self.datastore.upsert_notification(notification)
        return notification

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _student_enrollments(self, student_id: str) -> Iterable[Enrollment]:
        for enrollment in self.datastore.list_enrollments():
            if enrollment.student_id == student_id:
                yield enrollment

    def _course_lookup(self, course_id: str) -> Course:
        course = self.datastore.get_course(course_id)
        if not course:
            raise LookupError(f"Course '{course_id}' is missing from the data store")
        return course

    def _within_campus(self, latitude: float, longitude: float) -> bool:
        """Return ``True`` if the location is within the configured campus radius."""

        distance = self._haversine_distance(
            latitude,
            longitude,
            self._campus_latitude,
            self._campus_longitude,
        )
        return distance <= self._campus_radius_meters

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great-circle distance between two points in meters."""

        radius_earth_km = 6371.0
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance_km = radius_earth_km * c
        return distance_km * 1000
