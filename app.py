"""Entry point for running the student tracker as a small Flask web app."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from flask import Flask, render_template

from tracker import JSONDataStore, StudentService


def _default_data_path() -> Path:
    """Return the path to the bundled sample data file."""

    return Path(__file__).resolve().parent / "data" / "sample_data.json"


def _collect_highlights(student_service: StudentService, student_ids: Iterable[str]) -> List[Dict[str, str]]:
    """Generate a couple of friendly highlights for the landing page."""

    highlights: List[Dict[str, str]] = []
    for student_id in student_ids:
        gpa = student_service.calculate_gpa(student_id)
        if gpa is None:
            continue
        student = student_service.get_student(student_id)
        highlights.append(
            {
                "title": f"{student.name}'s GPA",
                "value": f"{gpa:.2f}",
            }
        )
        if len(highlights) == 2:
            break
    return highlights


def create_app(data_path: Path | None = None) -> Flask:
    """Create the Flask application instance."""

    datastore = JSONDataStore(data_path or _default_data_path())
    student_service = StudentService(datastore)

    app = Flask(__name__)

    @app.route("/")
    def index():
        students = datastore.list_students()
        courses = datastore.list_courses()
        professors = datastore.list_professors()
        stats = {
            "Students": len(students),
            "Courses": len(courses),
            "Professors": len(professors),
        }
        highlights = _collect_highlights(student_service, (student.student_id for student in students))

        return render_template(
            "index.html",
            stats=stats,
            students=students[:3],
            courses=courses[:3],
            highlights=highlights,
        )

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
