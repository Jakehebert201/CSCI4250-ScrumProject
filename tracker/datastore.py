"""Persistent storage helpers for the student tracker application."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from . import models


class DataStoreError(RuntimeError):
    """Raised when an operation on the data store fails."""


class JSONDataStore:
    """A JSON-backed data store for tracker entities."""

    def __init__(self, path: Path):
        self.path = path
        self._data: Dict[str, list] = {
            "students": [],
            "professors": [],
            "courses": [],
            "enrollments": [],
            "study_sessions": [],
            "notifications": [],
        }
        if self.path.exists():
            self._load()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._persist()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise DataStoreError("Failed to decode JSON data store") from exc

        for key in self._data:
            self._data[key] = raw.get(key, [])

    def _persist(self) -> None:
        serialized = {key: value for key, value in self._data.items()}
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(serialized, handle, indent=2)

    # ------------------------------------------------------------------
    # Entity retrieval helpers
    # ------------------------------------------------------------------
    def list_students(self) -> List[models.Student]:
        return [models.Student(**data) for data in self._data["students"]]

    def list_professors(self) -> List[models.Professor]:
        return [models.Professor(**data) for data in self._data["professors"]]

    def list_courses(self) -> List[models.Course]:
        return [models.Course(**data) for data in self._data["courses"]]

    def list_enrollments(self) -> List[models.Enrollment]:
        return [models.Enrollment.from_dict(data) for data in self._data["enrollments"]]

    def list_study_sessions(self) -> List[models.StudySession]:
        return [models.StudySession.from_dict(data) for data in self._data["study_sessions"]]

    def list_notifications(self) -> List[models.Notification]:
        return [models.Notification.from_dict(data) for data in self._data["notifications"]]

    def get_student(self, student_id: str) -> Optional[models.Student]:
        for student in self.list_students():
            if student.student_id == student_id:
                return student
        return None

    def get_professor(self, professor_id: str) -> Optional[models.Professor]:
        for professor in self.list_professors():
            if professor.professor_id == professor_id:
                return professor
        return None

    def get_course(self, course_id: str) -> Optional[models.Course]:
        for course in self.list_courses():
            if course.course_id == course_id:
                return course
        return None

    def get_enrollment(self, student_id: str, course_id: str) -> Optional[models.Enrollment]:
        for enrollment in self.list_enrollments():
            if enrollment.student_id == student_id and enrollment.course_id == course_id:
                return enrollment
        return None

    def get_active_study_session(self, student_id: str) -> Optional[models.StudySession]:
        for session in self.list_study_sessions():
            if session.student_id == student_id and session.end_time is None:
                return session
        return None

    def get_notification(self, notification_id: str) -> Optional[models.Notification]:
        for notification in self.list_notifications():
            if notification.notification_id == notification_id:
                return notification
        return None

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def upsert_student(self, student: models.Student) -> None:
        self._upsert("students", student, "student_id")

    def upsert_professor(self, professor: models.Professor) -> None:
        self._upsert("professors", professor, "professor_id")

    def upsert_course(self, course: models.Course) -> None:
        self._upsert("courses", course, "course_id")

    def upsert_enrollment(self, enrollment: models.Enrollment) -> None:
        serialized = enrollment.to_dict()
        self._upsert_raw("enrollments", serialized, ("student_id", "course_id"))

    def upsert_study_session(self, session: models.StudySession) -> None:
        serialized = session.to_dict()
        self._upsert_raw("study_sessions", serialized, "session_id")

    def upsert_notification(self, notification: models.Notification) -> None:
        serialized = notification.to_dict()
        self._upsert_raw("notifications", serialized, "notification_id")

    def _upsert(self, collection: str, entity, identifier: str) -> None:
        serialized = asdict(entity)
        self._upsert_raw(collection, serialized, identifier)

    def _upsert_raw(self, collection: str, serialized: dict, identifiers) -> None:
        if isinstance(identifiers, str):
            identifiers = (identifiers,)

        items = self._data[collection]
        for index, item in enumerate(items):
            if all(item.get(key) == serialized.get(key) for key in identifiers):
                items[index] = serialized
                self._persist()
                return

        items.append(serialized)
        self._persist()

    def upsert_many(self, students: Iterable[models.Student], professors: Iterable[models.Professor],
                    courses: Iterable[models.Course], enrollments: Iterable[models.Enrollment],
                    study_sessions: Iterable[models.StudySession] = (),
                    notifications: Iterable[models.Notification] = ()) -> None:
        self._data["students"] = [asdict(student) for student in students]
        self._data["professors"] = [asdict(professor) for professor in professors]
        self._data["courses"] = [asdict(course) for course in courses]
        self._data["enrollments"] = [enrollment.to_dict() for enrollment in enrollments]
        self._data["study_sessions"] = [session.to_dict() for session in study_sessions]
        self._data["notifications"] = [notification.to_dict() for notification in notifications]
        self._persist()

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def clear(self) -> None:
        for key in self._data:
            self._data[key] = []
        self._persist()
