#!/usr/bin/env python3
"""
Helper script to bootstrap the local database (and migrations folder).

Usage:
    python scripts/setup_database.py

The script will:
  * ensure the Alembic `migrations/` directory exists (running `flask db init` if needed)
  * run `flask db upgrade` so the SQLite database is on the latest schema

Run this after cloning the repo or whenever the migrations folder/database
needs to be recreated.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = REPO_ROOT / "tracker" / "app.py"  # matches docker: /app/tracker/app.py
if not APP_FILE.exists():
    APP_FILE = REPO_ROOT / "app.py"
MIGRATIONS_DIR = REPO_ROOT / "migrations"


def run_flask_command(*args: str) -> None:
    """Execute a Flask CLI command and surface errors clearly."""
    try:
        subprocess.run(
            ["flask", "--app", str(APP_FILE), *args],
            cwd=REPO_ROOT,
            check=True,
        )
    except FileNotFoundError:
        sys.exit("Error: `flask` executable not found. Activate your virtualenv first.")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Error: command {' '.join(exc.cmd)} failed with exit code {exc.returncode}.")


def ensure_migrations_directory() -> None:
    """Create the Alembic migrations folder if it does not already exist."""
    if MIGRATIONS_DIR.exists():
        print("✓ migrations/ already present; skipping `flask db init`.")
        return

    print("Creating migrations/ folder via `flask db init`…")
    run_flask_command("db", "init")
    print("✓ migrations/ created.")


def upgrade_database() -> None:
    """Apply the latest migrations to the database."""
    print("Applying latest migrations with `flask db upgrade`…")
    run_flask_command("db", "upgrade")
    print("✓ Database upgraded.")


def main() -> None:
    ensure_migrations_directory()
    upgrade_database()
    print("All done!")


if __name__ == "__main__":
    main()
