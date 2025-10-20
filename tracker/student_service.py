"""Student-facing services for the student tracker application."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from .datastore import JSONDataStore
from .models import Course, Enrollment, Student


class StudentNotFoundError(LookupError):
    """Raised when a student cannot be located in the data store."""


class StudentService:
    """Provides access to student-oriented grade and GPA views."""

    def __init__(self, datastore: JSONDataStore):
        self.datastore = datastore

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
