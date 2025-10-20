"""Data models for the student tracker application."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class AttendanceEntry:
    """Represents a single attendance record for a class session."""

    session_date: date
    status: str  # "present", "absent", "excused"

    def to_dict(self) -> dict:
        return {
            "session_date": self.session_date.isoformat(),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttendanceEntry":
        return cls(
            session_date=date.fromisoformat(data["session_date"]),
            status=data["status"],
        )


@dataclass
class Student:
    student_id: str
    name: str


@dataclass
class Professor:
    professor_id: str
    name: str


@dataclass
class Course:
    course_id: str
    name: str
    semester: str
    credits: float
    professor_id: str


@dataclass
class Enrollment:
    student_id: str
    course_id: str
    grade: Optional[float] = None  # Grade on a 0.0 - 4.0 scale
    attendance: List[AttendanceEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "grade": self.grade,
            "attendance": [record.to_dict() for record in self.attendance],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Enrollment":
        attendance = [AttendanceEntry.from_dict(entry) for entry in data.get("attendance", [])]
        return cls(
            student_id=data["student_id"],
            course_id=data["course_id"],
            grade=data.get("grade"),
            attendance=attendance,
        )
