"""Unit tests for student and professor services."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from tracker.datastore import JSONDataStore
from tracker.location_service import LocationService
from tracker.professor_service import AuthorizationError, ProfessorService
from tracker.student_service import (
    ActiveSessionExistsError,
    LocationValidationError,
    SessionNotFoundError,
    StudentNotFoundError,
    StudentService,
)


@pytest.fixture()
def datastore(tmp_path: Path) -> JSONDataStore:
    sample_path = PROJECT_ROOT / "data" / "sample_data.json"
    temp_file = tmp_path / "data.json"
    temp_file.write_bytes(sample_path.read_bytes())
    return JSONDataStore(temp_file)


def test_student_gpa(datastore: JSONDataStore) -> None:
    service = StudentService(datastore)
    overall = service.calculate_gpa("s1001")
    fall = service.calculate_gpa("s1001", semester="2023-Fall")
    assert overall == pytest.approx(3.68, abs=1e-2)
    assert fall == pytest.approx(3.8, abs=1e-2)


def test_student_grades_by_semester(datastore: JSONDataStore) -> None:
    service = StudentService(datastore)
    grades = service.get_grades_by_semester("s1001", "2023-Fall")
    course_ids = {record["course_id"] for record in grades}
    assert course_ids == {"c3001", "c3002"}


def test_student_filter_courses(datastore: JSONDataStore) -> None:
    service = StudentService(datastore)
    filtered = service.filter_courses("s1001", min_grade=3.8)
    assert {record["course_id"] for record in filtered} == {"c3002"}


def test_student_not_found(datastore: JSONDataStore) -> None:
    service = StudentService(datastore)
    with pytest.raises(StudentNotFoundError):
        service.calculate_gpa("missing")


def test_professor_grade_authorization(datastore: JSONDataStore) -> None:
    service = ProfessorService(datastore)
    with pytest.raises(AuthorizationError):
        service.add_or_update_grade(
            professor_id="p2002", student_id="s1001", course_id="c3001", grade=3.0
        )


def test_professor_grade_update(datastore: JSONDataStore) -> None:
    service = ProfessorService(datastore)
    updated = service.add_or_update_grade(
        professor_id="p2001", student_id="s1001", course_id="c3001", grade=3.9
    )
    assert updated.grade == 3.9
    reloaded = datastore.get_enrollment("s1001", "c3001")
    assert reloaded is not None
    assert reloaded.grade == 3.9


def test_professor_attendance(datastore: JSONDataStore) -> None:
    service = ProfessorService(datastore)
    updated = service.record_attendance(
        professor_id="p2001",
        student_id="s1002",
        course_id="c3001",
        session_date=date(2023, 9, 15),
        status="Present",
    )
    assert any(entry.session_date == date(2023, 9, 15) for entry in updated.attendance)
    assert datastore.get_enrollment("s1002", "c3001").attendance[-1].status == "present"


def test_professor_attendance_validation(datastore: JSONDataStore) -> None:
    service = ProfessorService(datastore)
    with pytest.raises(ValueError):
        service.record_attendance(
            professor_id="p2001",
            student_id="s1002",
            course_id="c3001",
            session_date=date(2023, 9, 15),
            status="tardy",
        )


def test_study_session_geofence(datastore: JSONDataStore) -> None:
    students = StudentService(datastore)
    session = students.start_study_session(
        "s1001", latitude=33.7550, longitude=-84.39
    )
    assert session.session_id
    assert datastore.get_active_study_session("s1001") is not None

    ended = students.end_study_session("s1001", latitude=33.7551, longitude=-84.3899)
    assert ended.end_time is not None
    stored_sessions = [s for s in datastore.list_study_sessions() if s.student_id == "s1001"]
    assert stored_sessions[0].end_time is not None


def test_study_session_validations(datastore: JSONDataStore) -> None:
    students = StudentService(datastore)
    with pytest.raises(LocationValidationError):
        students.start_study_session("s1001", latitude=34.0, longitude=-85.0)

    students.start_study_session("s1001", latitude=33.7550, longitude=-84.39)
    with pytest.raises(ActiveSessionExistsError):
        students.start_study_session("s1001", latitude=33.7550, longitude=-84.39)

    with pytest.raises(LocationValidationError):
        students.end_study_session("s1001", latitude=34.0, longitude=-84.0)

    students.end_study_session("s1001", latitude=33.7550, longitude=-84.39)
    with pytest.raises(SessionNotFoundError):
        students.end_study_session("s1001", latitude=33.7550, longitude=-84.39)


def test_notification_flow(datastore: JSONDataStore) -> None:
    professors = ProfessorService(datastore)
    students = StudentService(datastore)

    created = professors.send_notification(
        professor_id="p2001", title="Campus Update", message="Library will close early."
    )
    assert created.notification_id

    notifications = students.list_notifications("s1001")
    assert notifications
    assert notifications[0].title == "Campus Update"

    updated = students.mark_notification_read("s1001", created.notification_id)
    assert "s1001" in updated.read_by
    stored = datastore.get_notification(created.notification_id)
    assert stored is not None and "s1001" in stored.read_by


def test_location_service_records(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    responses = {
        "latitude": 10.0,
        "longitude": -20.5,
        "city": "Testville",
        "region": "North",
        "country": "Testland",
    }
    service = LocationService(data_dir, http_get=lambda _: responses)

    record = service.record_location("s1001")
    assert record.latitude == 10.0
    assert record.longitude == -20.5

    stored = service.get_location("s1001")
    assert stored is not None
    assert stored.city == "Testville"
    assert stored.country == "Testland"
