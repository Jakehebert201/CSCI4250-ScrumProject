# CSCI4250-ScrumProject

Student tracker application built in Python. The project models the first
iteration of the scrum backlog by supporting both the student and professor
experiences.

## Features

- **Students** can view grades grouped by semester, monitor GPA updates, and
  filter course history using multiple criteria.
- **Professors** can add or edit grades, record attendance, and the system
  enforces authorization so only the assigned instructor can modify a course.

## Project Layout

- `tracker/` – Core application package containing the data models and service
  layers for students and professors.
- `data/sample_data.json` – Example dataset used by the unit tests.
- `tests/` – Pytest suite covering the key user stories.

## Running the Tests

Install the dependencies (only `pytest` is required) and execute the test
suite:

```bash
python -m pip install -r requirements-dev.txt
pytest
```

## Development Environment

The services are designed to work with the `JSONDataStore` class which persists
tracker data to a JSON file. Point the datastore to your desired file location
to load or persist information for experimentation.
