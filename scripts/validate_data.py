#!/usr/bin/env python3
"""Validate dashboard CSV inputs and generated output using only the Python standard library."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

REQUIRED_FIELDS = {
    "record_id",
    "pathogen_id",
    "pathogen",
    "candidate",
    "stage_order",
    "status",
    "evidence_summary",
    "next_milestone",
    "evidence_type",
    "source_title",
    "source_url",
    "last_verified",
}
NCT_PATTERN = re.compile(r"^NCT\d{8}$", re.IGNORECASE)


def parse_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate bacterial dashboard data.")
    parser.add_argument("--data", default="data/pipeline.csv")
    parser.add_argument("--config", default="config/pathogens.json")
    args = parser.parse_args(argv)

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    profile_ids = {str(profile.get("id", "")).strip() for profile in config}
    errors: list[str] = []

    with Path(args.data).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_headers = sorted(REQUIRED_FIELDS - set(reader.fieldnames or []))
        if missing_headers:
            errors.append(f"Missing required column(s): {', '.join(missing_headers)}")
        rows = list(reader)

    seen_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        prefix = f"line {line_number}"
        record_id = str(row.get("record_id", "")).strip()
        if not record_id:
            errors.append(f"{prefix}: record_id is required")
        elif record_id in seen_ids:
            errors.append(f"{prefix}: duplicate record_id {record_id!r}")
        seen_ids.add(record_id)

        pathogen_id = str(row.get("pathogen_id", "")).strip()
        if pathogen_id not in profile_ids:
            errors.append(f"{prefix}: unknown pathogen_id {pathogen_id!r}")

        try:
            stage = int(float(str(row.get("stage_order", "")).strip()))
            if stage not in range(8):
                errors.append(f"{prefix}: stage_order must be 0–7")
        except ValueError:
            stage = -1
            errors.append(f"{prefix}: stage_order is not numeric")

        status_type = str(row.get("status_type", "")).strip()
        source_url = str(row.get("source_url", "")).strip()
        source_title = str(row.get("source_title", "")).strip()
        if status_type != "Gap row" and stage != 0:
            if not source_url.startswith(("https://", "http://")):
                errors.append(f"{prefix}: source_url must be an HTTP(S) URL")
            if not source_title:
                errors.append(f"{prefix}: source_title is required")

        verified = str(row.get("last_verified", "")).strip()
        if not verified or not parse_date(verified):
            errors.append(f"{prefix}: last_verified must use YYYY-MM-DD")

        trial_id = str(row.get("trial_id", "")).strip()
        if trial_id and not NCT_PATTERN.match(trial_id):
            errors.append(f"{prefix}: trial_id {trial_id!r} is not an NCT identifier")

        for field in ("candidate", "pathogen", "evidence_summary", "next_milestone", "evidence_type"):
            if not str(row.get(field, "")).strip():
                errors.append(f"{prefix}: {field} is required")

    covered = {str(row.get("pathogen_id", "")).strip() for row in rows}
    missing_profiles = sorted(profile_ids - covered)
    if missing_profiles:
        errors.append(f"No output row for configured pathogen(s): {', '.join(missing_profiles)}")

    if errors:
        print("Data validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(rows)} rows across {len(covered)} pathogen profiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
