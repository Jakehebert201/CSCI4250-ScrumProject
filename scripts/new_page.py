#!/usr/bin/env python3
"""Generate boilerplate templates for the /app/<slug>/ dynamic route."""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import sys
from typing import List, Dict

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates" / "pages"
MANIFEST_PATH = ROOT / "pages.json"

STUB = """{% extends 'base.html' %}
{% block title %}{title}{% endblock %}
{% block content %}
<section class="card">
    <h1>{title}</h1>
    <p>New page generated {timestamp}.</p>
</section>
{% endblock %}
"""


def _slugify(raw: str) -> str:
    slug = raw.strip().lower().replace(" ", "-")
    slug = slug.strip("/")
    slug = slug.replace("..", "")
    if not slug:
        raise ValueError("Slug cannot be empty")
    return slug


def _write_manifest_entry(slug: str, title: str) -> None:
    try:
        data: List[Dict[str, str]] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = []
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Manifest JSON invalid: {exc}")

    if not any(item.get("slug") == slug for item in data):
        data.append({"slug": slug, "title": title})
        MANIFEST_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/new_page.py <slug> [Title...]")
        raise SystemExit(1)

    try:
        slug = _slugify(sys.argv[1])
    except ValueError as exc:
        raise SystemExit(str(exc))

    title = " ".join(sys.argv[2:]).strip() or slug.replace("-", " ").title()

    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    target = TEMPLATE_DIR / f"{slug}.html"

    if target.exists():
        print(f"Exists: {target}")
        return

    timestamp = _dt.datetime.utcnow().isoformat() + "Z"
    target.write_text(STUB.format(title=title, timestamp=timestamp), encoding="utf-8")
    print(f"Created template: {target.relative_to(ROOT)}")

    _write_manifest_entry(slug, title)
    print(f"Updated manifest: {MANIFEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
