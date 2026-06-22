#!/usr/bin/env python3
"""Build the static GitHub Pages dashboard from generated CSV data."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

STAGES = [
    {"order": 0, "short": "Gap", "label": "Evidence gap / no mapped human-vaccine pathway"},
    {"order": 1, "short": "Discovery", "label": "Discovery / translational"},
    {"order": 2, "short": "Preclinical", "label": "Preclinical / manufacturing-enabling"},
    {"order": 3, "short": "Phase 1", "label": "Phase 1"},
    {"order": 4, "short": "Phase 2", "label": "Phase 2"},
    {"order": 5, "short": "Efficacy", "label": "Efficacy / Phase 3"},
    {"order": 6, "short": "Authorized", "label": "Regulatory authorization / WHO prequalification"},
    {"order": 7, "short": "In use", "label": "Programmatic use / stockpile / post-licensure"},
]

INTEGER_FIELDS = {"stage_order", "enrollment", "supporting_record_count"}


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows: list[dict[str, Any]] = []
        for raw in csv.DictReader(handle):
            row: dict[str, Any] = dict(raw)
            for field in INTEGER_FIELDS:
                value = str(row.get(field, "")).strip()
                if not value:
                    row[field] = None if field == "enrollment" else 0
                    continue
                try:
                    row[field] = int(float(value))
                except ValueError:
                    row[field] = value
            rows.append(row)
        return rows


def compact_json(value: Any) -> str:
    # Prevent data strings from prematurely closing the embedding script tag.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the static bacterial vaccine dashboard.")
    parser.add_argument("--data", default="data/pipeline.csv", help="Generated pipeline CSV")
    parser.add_argument("--config", default="config/pathogens.json", help="Pathogen configuration JSON")
    parser.add_argument("--template", default="scripts/dashboard_template.html", help="Dashboard HTML template")
    parser.add_argument("--report", default="reports/automation_summary.md", help="Automation report")
    parser.add_argument("--out-dir", default="public", help="Output directory")
    args = parser.parse_args(argv)

    data_path = Path(args.data)
    config_path = Path(args.config)
    template_path = Path(args.template)
    report_path = Path(args.report)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_csv(data_path)
    profiles = json.loads(config_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")
    built_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    replacements = {
        "__DATA_JSON__": compact_json(rows),
        "__PATHOGENS_JSON__": compact_json(profiles),
        "__STAGES_JSON__": compact_json(STAGES),
        "__BUILT_AT__": built_at,
        "__CSV_NAME__": "bacterial_vaccine_development_pipeline_data.csv",
        "__REPORT_NAME__": "automation_summary.md",
    }
    html = template
    for marker, value in replacements.items():
        if marker not in html:
            raise ValueError(f"Required template marker not found: {marker}")
        html = html.replace(marker, value)

    index_path = out_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    shutil.copyfile(data_path, out_dir / replacements["__CSV_NAME__"])
    shutil.copyfile(config_path, out_dir / "pathogens.json")
    if report_path.exists():
        shutil.copyfile(report_path, out_dir / replacements["__REPORT_NAME__"])

    print(f"Built {index_path} with {len(rows)} records and {len(profiles)} pathogen profiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
