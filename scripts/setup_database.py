#!/usr/bin/env python3
"""
Helper script to bootstrap the local SQLite database without relying on Alembic.

Usage:
    python scripts/setup_database.py

The script will:
  * ensure the SQLite database path (and parent directories) exists
  * work around known sample-data dependencies
  * initialize the schema by invoking the application's app factory
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ArgumentError

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "instance" / "studenttracker.db"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import studenttracker as tracker  # noqa: E402
from studenttracker import create_app, db  # noqa: E402,F401


def _candidate_sqlite_paths() -> list[Path]:
    """Resolve the SQLite file paths that might be in use."""
    db_url = os.environ.get("DATABASE_URL")
    paths: list[Path] = []

    if db_url:
        try:
            url = make_url(db_url)
        except ArgumentError as exc:
            print(f"Warning: could not parse DATABASE_URL ({exc}); falling back to default.")
        else:
            if url.drivername.startswith("sqlite") and url.database:
                db_path = Path(url.database)
                if not db_path.is_absolute():
                    db_path = (REPO_ROOT / db_path).resolve()
                paths.append(db_path)

    if not paths:
        paths.append(DEFAULT_DB_PATH)

    return paths


def _prepare_sqlite_targets() -> None:
    """Create parent directories and placeholder files for SQLite databases."""
    for db_path in _candidate_sqlite_paths():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        if not db_path.exists():
            db_path.touch(mode=0o600)
        else:
            # Ensure permissive-enough mode for local development
            try:
                db_path.chmod(0o600)
            except PermissionError:
                print(f"Warning: unable to adjust permissions for {db_path}.")


def _patch_sample_data_dependencies() -> None:
    """Provide missing globals expected by create_sample_data."""
    from datetime import timedelta

    if not hasattr(tracker, "timedelta"):
        tracker.timedelta = timedelta


def main() -> None:
    _prepare_sqlite_targets()
    _patch_sample_data_dependencies()

    try:
        app = create_app()
    except Exception as exc:  # pragma: no cover - surfaced for CLI use
        print("Failed to initialize application:", exc, file=sys.stderr)
        raise

    with app.app_context():
        db_url = app.config["SQLALCHEMY_DATABASE_URI"]
        print(f"Database initialized at: {db_url}")


if __name__ == "__main__":
    main()
