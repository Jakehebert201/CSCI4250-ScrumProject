"""Data models for the student tracker application."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
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


@dataclass
class StudySession:
    """Represents a timed study session for a student."""

    session_id: str
    student_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "start_latitude": self.start_latitude,
            "start_longitude": self.start_longitude,
            "end_latitude": self.end_latitude,
            "end_longitude": self.end_longitude,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StudySession":
        return cls(
            session_id=data["session_id"],
            student_id=data["student_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            start_latitude=data.get("start_latitude"),
            start_longitude=data.get("start_longitude"),
            end_latitude=data.get("end_latitude"),
            end_longitude=data.get("end_longitude"),
        )


@dataclass
class Notification:
    """Represents a broadcast notification sent by a professor."""

    notification_id: str
    title: str
    message: str
    sender_id: str
    sent_at: datetime
    read_by: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "message": self.message,
            "sender_id": self.sender_id,
            "sent_at": self.sent_at.isoformat(),
            "read_by": list(self.read_by),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Notification":
        return cls(
            notification_id=data["notification_id"],
            title=data["title"],
            message=data["message"],
            sender_id=data["sender_id"],
            sent_at=datetime.fromisoformat(data["sent_at"]),
            read_by=list(data.get("read_by", [])),
        )
