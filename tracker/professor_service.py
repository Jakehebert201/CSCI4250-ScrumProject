"""Professor-facing services for the student tracker application."""
from __future__ import annotations

from datetime import date
from typing import Optional

from .datastore import JSONDataStore
from .models import AttendanceEntry, Course, Enrollment


class AuthorizationError(PermissionError):
    """Raised when a professor attempts to edit a course they do not own."""


class ProfessorService:
    """Provide grade and attendance management for professors."""

    def __init__(self, datastore: JSONDataStore):
        self.datastore = datastore

    # ------------------------------------------------------------------
    # Grade management
    # ------------------------------------------------------------------
    def add_or_update_grade(
        self,
        *,
        professor_id: str,
        student_id: str,
        course_id: str,
        grade: float,
    ) -> Enrollment:
        """Add a new grade or update an existing one for a student."""

        course = self._authorized_course(professor_id, course_id)
        enrollment = self.datastore.get_enrollment(student_id, course_id)
        if not enrollment:
            enrollment = Enrollment(student_id=student_id, course_id=course.course_id, grade=grade)
        else:
            enrollment.grade = grade
        self._validate_grade(enrollment.grade)
        self.datastore.upsert_enrollment(enrollment)
        return enrollment

    # ------------------------------------------------------------------
    # Attendance management
    # ------------------------------------------------------------------
    def record_attendance(
        self,
        *,
        professor_id: str,
        student_id: str,
        course_id: str,
        session_date: date,
        status: str,
    ) -> Enrollment:
        """Record attendance for a student in a course session."""

        enrollment = self.datastore.get_enrollment(student_id, course_id)
        if enrollment is None:
            # Ensure the professor is authorized even if we need to create a record.
            course = self._authorized_course(professor_id, course_id)
            enrollment = Enrollment(student_id=student_id, course_id=course.course_id)
        else:
            self._authorized_course(professor_id, course_id)

        normalized_status = status.lower()
        if normalized_status not in {"present", "absent", "excused"}:
            raise ValueError("Attendance status must be 'present', 'absent', or 'excused'")

        # Remove any existing record for the given date and append the new entry
        enrollment.attendance = [
            entry for entry in enrollment.attendance if entry.session_date != session_date
        ]
        enrollment.attendance.append(
            AttendanceEntry(session_date=session_date, status=normalized_status)
        )
        enrollment.attendance.sort(key=lambda entry: entry.session_date)
        self.datastore.upsert_enrollment(enrollment)
        return enrollment

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _authorized_course(self, professor_id: str, course_id: str) -> Course:
        course = self.datastore.get_course(course_id)
        if not course:
            raise LookupError(f"Course '{course_id}' not found")
        if course.professor_id != professor_id:
            raise AuthorizationError(
                f"Professor '{professor_id}' is not authorized to edit course '{course_id}'"
            )
        return course

    @staticmethod
    def _validate_grade(grade: Optional[float]) -> None:
        if grade is None:
            return
        if not 0.0 <= grade <= 4.0:
            raise ValueError("Grades must be provided on a 0.0 - 4.0 scale")
