"""Unit tests for student and professor services."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from tracker.datastore import JSONDataStore
from tracker.professor_service import AuthorizationError, ProfessorService
from tracker.student_service import StudentNotFoundError, StudentService


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
