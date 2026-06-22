#!/usr/bin/env python3
"""Refresh the priority bacterial pathogen vaccine pipeline.

The script merges manually curated seed rows with conservative signals from the
ClinicalTrials.gov API v2. Automated registry records can populate clinical
stages only; they can never create authorization, WHO-prequalification, or
programmatic-use claims.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

API_URL = "https://clinicaltrials.gov/api/v2/studies"
USER_AGENT = "priority-bacterial-pathogen-dashboard/1.0 (+GitHub Pages research dashboard)"

STAGE_LABELS = {
    0: "Evidence gap / no mapped human-vaccine pathway",
    1: "Discovery / translational",
    2: "Preclinical / manufacturing-enabling",
    3: "Phase 1",
    4: "Phase 2",
    5: "Efficacy / Phase 3",
    6: "Regulatory authorization / WHO prequalification",
    7: "Programmatic use / stockpile / post-licensure",
}

OUTPUT_FIELDS = [
    "record_id",
    "pathogen_id",
    "pathogen",
    "pathogen_group",
    "priority_rationale",
    "target_scope",
    "candidate",
    "stage_order",
    "stage",
    "status",
    "status_type",
    "phase",
    "platform",
    "sponsor",
    "trial_id",
    "serovars",
    "population",
    "countries",
    "enrollment",
    "start_date",
    "primary_completion_date",
    "registry_last_updated",
    "evidence_summary",
    "next_milestone",
    "evidence_type",
    "source_title",
    "source_url",
    "source_date",
    "last_verified",
    "automation_notes",
    "supporting_record_count",
]

STATUS_LABELS = {
    "NOT_YET_RECRUITING": "Not yet recruiting",
    "RECRUITING": "Recruiting",
    "ENROLLING_BY_INVITATION": "Enrolling by invitation",
    "ACTIVE_NOT_RECRUITING": "Active, not recruiting",
    "SUSPENDED": "Suspended",
    "TERMINATED": "Terminated",
    "COMPLETED": "Completed",
    "WITHDRAWN": "Withdrawn",
    "UNKNOWN": "Unknown",
    "AVAILABLE": "Available",
    "NO_LONGER_AVAILABLE": "No longer available",
    "TEMPORARILY_NOT_AVAILABLE": "Temporarily not available",
    "APPROVED_FOR_MARKETING": "Approved for marketing",
    "WITHHELD": "Withheld",
}

PHASE_STAGE = {
    "EARLY_PHASE1": 3,
    "PHASE1": 3,
    "PHASE2": 4,
    "PHASE3": 5,
    # Automated records are deliberately capped at stage 5. A Phase 4 label
    # alone is not accepted as proof of a target-specific authorization claim.
    "PHASE4": 5,
    "NA": 3,
}

PHASE_LABEL = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE2": "Phase 2",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
    "NA": "Not applicable / not reported",
}

ACTIVE_STATUS_CODES = {
    "NOT_YET_RECRUITING",
    "RECRUITING",
    "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
}

VACCINE_INDICATORS = (
    "vaccine",
    "vaccination",
    "immunization",
    "immunisation",
    "gmma",
    "bioconjugate",
    "conjugate vaccine",
    "whole-cell vaccine",
    "subunit vaccine",
    "rf1v",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_date_now() -> str:
    return utc_now().date().isoformat()


def iso_timestamp_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def nested(mapping: Mapping[str, Any], *keys: str, default: Any = "") -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return default
        current = current[key]
    return current


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def normalize_row(row: MutableMapping[str, Any]) -> dict[str, str]:
    normalized = {field: safe_text(row.get(field, "")) for field in OUTPUT_FIELDS}
    try:
        stage_order = int(float(normalized.get("stage_order") or 0))
    except ValueError:
        stage_order = 0
    stage_order = max(0, min(7, stage_order))
    normalized["stage_order"] = str(stage_order)
    normalized["stage"] = STAGE_LABELS[stage_order]
    try:
        supporting = int(float(normalized.get("supporting_record_count") or 0))
    except ValueError:
        supporting = 0
    normalized["supporting_record_count"] = str(max(0, supporting))
    return normalized


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(normalize_row(dict(row)))


def build_request_url(query: str, page_token: str | None, page_size: int) -> str:
    params: dict[str, str | int] = {
        "query.term": query,
        "format": "json",
        "pageSize": page_size,
        "countTotal": "true",
        "sort": "LastUpdatePostDate:desc",
    }
    if page_token:
        params["pageToken"] = page_token
    return f"{API_URL}?{urllib.parse.urlencode(params)}"


def fetch_query(
    query: str,
    *,
    max_pages: int,
    page_size: int,
    timeout: int,
    pause_seconds: float,
) -> tuple[list[dict[str, Any]], int]:
    studies: list[dict[str, Any]] = []
    page_token: str | None = None
    reported_total = 0

    for page_number in range(1, max_pages + 1):
        request = urllib.request.Request(
            build_request_url(query, page_token, page_size),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
        if page_number == 1:
            try:
                reported_total = int(payload.get("totalCount") or 0)
            except (TypeError, ValueError):
                reported_total = 0
        page_studies = payload.get("studies") or []
        if isinstance(page_studies, list):
            studies.extend(item for item in page_studies if isinstance(item, dict))
        page_token = safe_text(payload.get("nextPageToken")) or None
        if not page_token:
            break
        if pause_seconds:
            time.sleep(pause_seconds)

    return studies, reported_total


def flatten_interventions(study: Mapping[str, Any]) -> list[dict[str, str]]:
    raw = nested(study, "protocolSection", "armsInterventionsModule", "interventions", default=[])
    results: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return results
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        results.append(
            {
                "name": safe_text(item.get("name")),
                "type": safe_text(item.get("type")),
                "description": safe_text(item.get("description")),
            }
        )
    return results


def study_blob(study: Mapping[str, Any]) -> tuple[str, str]:
    identification = nested(study, "protocolSection", "identificationModule", default={})
    conditions = nested(study, "protocolSection", "conditionsModule", default={})
    description = nested(study, "protocolSection", "descriptionModule", default={})
    interventions = flatten_interventions(study)

    primary_parts = [
        safe_text(identification.get("briefTitle")) if isinstance(identification, Mapping) else "",
        safe_text(identification.get("officialTitle")) if isinstance(identification, Mapping) else "",
        safe_text(conditions.get("conditions")) if isinstance(conditions, Mapping) else "",
        safe_text(conditions.get("keywords")) if isinstance(conditions, Mapping) else "",
        safe_text([item["name"] for item in interventions]),
    ]
    full_parts = primary_parts + [
        safe_text(description.get("briefSummary")) if isinstance(description, Mapping) else "",
        safe_text([item["description"] for item in interventions]),
    ]
    return " ".join(primary_parts).lower(), " ".join(full_parts).lower()


def is_target_match(profile: Mapping[str, Any], primary_blob: str, full_blob: str) -> tuple[bool, str]:
    pathogen_id = safe_text(profile.get("id"))
    terms = [safe_text(term).lower() for term in profile.get("match_terms", []) if safe_text(term)]
    matched = [term for term in terms if term in full_blob]
    if not matched:
        return False, "no configured target term"

    if pathogen_id == "klebsiella_pneumoniae" and "klebsiella" not in full_blob:
        return False, "pneumoniae ambiguity without Klebsiella"
    if pathogen_id == "ints_salmonella":
        ints_markers = (
            "nontyphoidal salmonella",
            "non-typhoidal salmonella",
            "ints",
            "enteritidis",
            "typhimurium",
        )
        if not any(marker in full_blob for marker in ints_markers):
            return False, "typhoid-only or non-iNTS Salmonella record"
    if pathogen_id == "yersinia_pestis" and not any(
        marker in full_blob for marker in ("plague", "yersinia pestis", "rf1v")
    ):
        return False, "not a plague vaccine record"

    exclusions = [safe_text(term).lower() for term in profile.get("exclude_terms", []) if safe_text(term)]
    # Only reject exclusions that dominate the title/intervention area and where no
    # configured target term appears there. This avoids dropping valid trials that
    # merely mention a comparator or background concept in the longer summary.
    if exclusions and any(term in primary_blob for term in exclusions):
        if not any(term in primary_blob for term in terms):
            return False, "configured exclusion term"

    return True, matched[0]


def vaccine_relevant(study: Mapping[str, Any], primary_blob: str, full_blob: str) -> bool:
    study_type = safe_text(nested(study, "protocolSection", "designModule", "studyType")).upper()
    if study_type and study_type != "INTERVENTIONAL":
        return False
    # Require an explicit vaccine signal. A generic BIOLOGICAL intervention or
    # the word “immunogenicity” alone can describe antibodies and therapeutics.
    return any(indicator in full_blob for indicator in VACCINE_INDICATORS)


def phase_details(study: Mapping[str, Any]) -> tuple[int, str, list[str]]:
    phases_raw = nested(study, "protocolSection", "designModule", "phases", default=[])
    phases = [safe_text(item).upper() for item in phases_raw] if isinstance(phases_raw, list) else []
    if not phases:
        phases = ["NA"]
    stage = max(PHASE_STAGE.get(item, 3) for item in phases)
    stage = min(stage, 5)
    labels = [PHASE_LABEL.get(item, item.replace("_", " ").title()) for item in phases]
    return stage, " / ".join(dict.fromkeys(labels)), phases


def candidate_name(study: Mapping[str, Any], profile: Mapping[str, Any]) -> str:
    interventions = flatten_interventions(study)
    match_terms = [safe_text(term).lower() for term in profile.get("match_terms", [])]
    preferred: list[str] = []
    fallback: list[str] = []
    for item in interventions:
        name = item["name"]
        if not name:
            continue
        low = name.lower()
        if low in {"placebo", "saline", "control", "standard of care"}:
            continue
        fallback.append(name)
        if any(indicator in low for indicator in VACCINE_INDICATORS) or any(term in low for term in match_terms):
            preferred.append(name)
    names = preferred or fallback
    unique = list(dict.fromkeys(names))
    if unique:
        return "; ".join(unique[:3])
    return safe_text(nested(study, "protocolSection", "identificationModule", "briefTitle")) or "Unnamed vaccine candidate"


def infer_platform(study: Mapping[str, Any]) -> str:
    blob = " ".join(
        f"{item.get('name', '')} {item.get('description', '')}" for item in flatten_interventions(study)
    ).lower()
    patterns = [
        ("gmma", "Generalized Modules for Membrane Antigens (GMMA)"),
        ("bioconjugate", "Bioconjugate vaccine"),
        ("conjugate", "Conjugate vaccine"),
        ("live attenuated", "Live attenuated vaccine"),
        ("inactivated", "Inactivated vaccine"),
        ("killed whole", "Killed whole-cell vaccine"),
        ("mrna", "mRNA vaccine"),
        ("dna vaccine", "DNA vaccine"),
        ("protein", "Recombinant protein / subunit vaccine"),
        ("subunit", "Subunit vaccine"),
        ("rf1v", "Recombinant F1-V subunit vaccine"),
    ]
    for needle, label in patterns:
        if needle in blob:
            return label
    return "Biological vaccine candidate"


def date_value(study: Mapping[str, Any], module_key: str) -> str:
    return safe_text(nested(study, "protocolSection", "statusModule", module_key, "date"))


def countries_value(study: Mapping[str, Any]) -> str:
    locations = nested(study, "protocolSection", "contactsLocationsModule", "locations", default=[])
    countries: list[str] = []
    if isinstance(locations, list):
        for location in locations:
            if isinstance(location, Mapping):
                country = safe_text(location.get("country"))
                if country:
                    countries.append(country)
    return "; ".join(sorted(set(countries)))


def population_value(study: Mapping[str, Any]) -> str:
    eligibility = nested(study, "protocolSection", "eligibilityModule", default={})
    if not isinstance(eligibility, Mapping):
        return ""
    minimum = safe_text(eligibility.get("minimumAge"))
    maximum = safe_text(eligibility.get("maximumAge"))
    sex = safe_text(eligibility.get("sex"))
    healthy = eligibility.get("healthyVolunteers")
    parts: list[str] = []
    if minimum or maximum:
        parts.append(f"Age {minimum or 'not stated'} to {maximum or 'not stated'}")
    if sex:
        parts.append(sex.title())
    if healthy is True:
        parts.append("healthy volunteers accepted")
    return "; ".join(parts)


def next_milestone(stage: int, status_code: str) -> str:
    if status_code in {"TERMINATED", "WITHDRAWN", "SUSPENDED"}:
        return "Clarify programme continuation, the reason for interruption, and any replacement development plan."
    if status_code == "COMPLETED":
        return "Review or publish results and confirm the next registered development milestone."
    if stage <= 3:
        return "Complete early clinical assessment and define dose, schedule, and target population for Phase 2."
    if stage == 4:
        return "Complete Phase 2 objectives and determine readiness for an efficacy-stage programme."
    return "Complete efficacy-stage development and prepare a source-backed regulatory strategy."


def registry_row(study: Mapping[str, Any], profile: Mapping[str, Any], match_reason: str) -> dict[str, Any]:
    identification = nested(study, "protocolSection", "identificationModule", default={})
    status_module = nested(study, "protocolSection", "statusModule", default={})
    sponsor_module = nested(study, "protocolSection", "sponsorCollaboratorsModule", default={})
    design_module = nested(study, "protocolSection", "designModule", default={})

    nct_id = safe_text(identification.get("nctId")) if isinstance(identification, Mapping) else ""
    title = safe_text(identification.get("briefTitle")) if isinstance(identification, Mapping) else ""
    overall_code = safe_text(status_module.get("overallStatus")).upper() if isinstance(status_module, Mapping) else ""
    status = STATUS_LABELS.get(overall_code, overall_code.replace("_", " ").title() or "Unknown")
    stage, phase, raw_phases = phase_details(study)
    sponsor = ""
    if isinstance(sponsor_module, Mapping):
        lead = sponsor_module.get("leadSponsor")
        if isinstance(lead, Mapping):
            sponsor = safe_text(lead.get("name"))
    enrollment = ""
    if isinstance(design_module, Mapping):
        enrollment_info = design_module.get("enrollmentInfo")
        if isinstance(enrollment_info, Mapping):
            enrollment = safe_text(enrollment_info.get("count"))

    last_updated = date_value(study, "lastUpdatePostDateStruct")
    source_date = last_updated or date_value(study, "studyFirstPostDateStruct")
    phase_note = ", ".join(raw_phases)
    evidence_summary = (
        f"ClinicalTrials.gov lists {title or nct_id} as {phase or 'a clinical study'} "
        f"with status {status}. This row was matched to {safe_text(profile.get('name'))} "
        f"using the configured term “{match_reason}”."
    )
    notes = (
        "Automated ClinicalTrials.gov match. Verify target specificity, intervention identity, and registry status. "
        f"Automated stage signal ({phase_note or 'phase not reported'}) is capped at stage 5; stages 6–7 require curated official evidence."
    )

    return {
        "record_id": (
            f"ctg-{nct_id.lower()}"
            if nct_id
            else f"ctg-unnamed-{hashlib.sha1(title.encode('utf-8')).hexdigest()[:12]}"
        ),
        "pathogen_id": safe_text(profile.get("id")),
        "pathogen": safe_text(profile.get("name")),
        "pathogen_group": safe_text(profile.get("group")),
        "priority_rationale": safe_text(profile.get("priority_rationale")),
        "target_scope": safe_text(profile.get("target_scope")),
        "candidate": candidate_name(study, profile),
        "stage_order": stage,
        "stage": STAGE_LABELS[stage],
        "status": status,
        "status_type": "Clinical candidate",
        "phase": phase,
        "platform": infer_platform(study),
        "sponsor": sponsor,
        "trial_id": nct_id,
        "serovars": "",
        "population": population_value(study),
        "countries": countries_value(study),
        "enrollment": enrollment,
        "start_date": date_value(study, "startDateStruct"),
        "primary_completion_date": date_value(study, "primaryCompletionDateStruct"),
        "registry_last_updated": last_updated,
        "evidence_summary": evidence_summary,
        "next_milestone": next_milestone(stage, overall_code),
        "evidence_type": "Automated ClinicalTrials.gov",
        "source_title": f"ClinicalTrials.gov: {nct_id}" if nct_id else "ClinicalTrials.gov record",
        "source_url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "https://clinicaltrials.gov/",
        "source_date": source_date,
        "last_verified": iso_date_now(),
        "automation_notes": notes,
        "supporting_record_count": 1,
        "_active": overall_code in ACTIVE_STATUS_CODES,
    }


def merge_registry_rows(
    curated_rows: list[dict[str, str]], registry_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int, int]:
    rows: list[dict[str, Any]] = [dict(row) for row in curated_rows]
    trial_index = {
        safe_text(row.get("trial_id")).upper(): index
        for index, row in enumerate(rows)
        if safe_text(row.get("trial_id"))
    }
    merged = 0
    added = 0

    for auto in registry_rows:
        trial_id = safe_text(auto.get("trial_id")).upper()
        if trial_id and trial_id in trial_index:
            target = rows[trial_index[trial_id]]
            for field in (
                "status",
                "phase",
                "countries",
                "enrollment",
                "start_date",
                "primary_completion_date",
                "registry_last_updated",
                "last_verified",
            ):
                value = safe_text(auto.get(field))
                if value:
                    target[field] = value
            try:
                target_stage = int(float(safe_text(target.get("stage_order")) or 0))
            except ValueError:
                target_stage = 0
            try:
                auto_stage = int(float(safe_text(auto.get("stage_order")) or 0))
            except ValueError:
                auto_stage = 0
            target["stage_order"] = max(target_stage, min(auto_stage, 5))
            target["stage"] = STAGE_LABELS[int(target["stage_order"])]
            existing_notes = safe_text(target.get("automation_notes"))
            refresh_note = (
                f"Registry refreshed {iso_date_now()} from {trial_id}; live status: {safe_text(auto.get('status'))}; "
                f"registry last updated: {safe_text(auto.get('registry_last_updated')) or 'not reported'}."
            )
            target["automation_notes"] = " ".join(part for part in (existing_notes, refresh_note) if part)
            try:
                supporting = int(float(safe_text(target.get("supporting_record_count")) or 0))
            except ValueError:
                supporting = 0
            target["supporting_record_count"] = max(1, supporting)
            merged += 1
        else:
            rows.append(auto)
            if trial_id:
                trial_index[trial_id] = len(rows) - 1
            added += 1

    return rows, merged, added


def ensure_gap_rows(rows: list[dict[str, Any]], profiles: Sequence[Mapping[str, Any]]) -> int:
    present = {safe_text(row.get("pathogen_id")) for row in rows}
    added = 0
    for profile in profiles:
        pathogen_id = safe_text(profile.get("id"))
        if pathogen_id in present:
            continue
        rows.append(
            {
                "record_id": f"gap-{pathogen_id}",
                "pathogen_id": pathogen_id,
                "pathogen": safe_text(profile.get("name")),
                "pathogen_group": safe_text(profile.get("group")),
                "priority_rationale": safe_text(profile.get("priority_rationale")),
                "target_scope": safe_text(profile.get("target_scope")),
                "candidate": "No mapped candidate record",
                "stage_order": 0,
                "status": "Evidence gap",
                "status_type": "Gap row",
                "phase": "",
                "platform": "",
                "sponsor": "",
                "trial_id": "",
                "serovars": "",
                "population": "",
                "countries": "",
                "enrollment": "",
                "start_date": "",
                "primary_completion_date": "",
                "registry_last_updated": "",
                "evidence_summary": "No candidate or official pathway row is currently mapped for this target in the configured dataset.",
                "next_milestone": "Conduct a manual landscape review and add source-backed rows.",
                "evidence_type": "Generated gap row",
                "source_title": "",
                "source_url": "",
                "source_date": "",
                "last_verified": iso_date_now(),
                "automation_notes": "Generated because no curated or automated record was available.",
                "supporting_record_count": 0,
            }
        )
        added += 1
    return added


def sort_rows(rows: list[dict[str, Any]], profiles: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    order = {safe_text(profile.get("id")): int(profile.get("order") or 999) for profile in profiles}

    def key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        try:
            stage = int(float(safe_text(row.get("stage_order")) or 0))
        except ValueError:
            stage = 0
        return (
            order.get(safe_text(row.get("pathogen_id")), 999),
            -stage,
            safe_text(row.get("candidate")).lower(),
            safe_text(row.get("trial_id")),
        )

    return sorted(rows, key=key)


def write_report(
    path: Path,
    *,
    rows: Sequence[Mapping[str, Any]],
    profiles: Sequence[Mapping[str, Any]],
    network_enabled: bool,
    query_stats: Sequence[Mapping[str, Any]],
    errors: Sequence[str],
    merged: int,
    added: int,
    gap_rows: int,
) -> None:
    by_pathogen: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_pathogen[safe_text(row.get("pathogen_id"))].append(row)

    lines = [
        "# Automation summary",
        "",
        f"Generated: `{iso_timestamp_now()}`",
        "",
        "## Run status",
        "",
        f"- Network refresh requested: **{'yes' if network_enabled else 'no'}**",
        f"- Final rows: **{len(rows)}**",
        f"- Curated rows updated from matching registry IDs: **{merged}**",
        f"- Newly discovered registry rows added: **{added}**",
        f"- Generated gap rows: **{gap_rows}**",
        "",
    ]
    if query_stats:
        lines.extend(["## ClinicalTrials.gov queries", "", "| Pathogen | Query | API total | Retrieved | Accepted |", "|---|---|---:|---:|---:|"])
        for stat in query_stats:
            lines.append(
                f"| {safe_text(stat.get('pathogen'))} | `{safe_text(stat.get('query'))}` | "
                f"{safe_text(stat.get('reported_total')) or '0'} | {safe_text(stat.get('retrieved')) or '0'} | "
                f"{safe_text(stat.get('accepted')) or '0'} |"
            )
        lines.append("")
    if errors:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")

    lines.extend(["## Rows by pathogen", "", "| Pathogen | Rows | Highest stage |", "|---|---:|---|"])
    for profile in profiles:
        target_rows = by_pathogen.get(safe_text(profile.get("id")), [])
        stages = []
        for row in target_rows:
            try:
                stages.append(int(float(safe_text(row.get("stage_order")) or 0)))
            except ValueError:
                stages.append(0)
        highest = max(stages, default=0)
        lines.append(f"| {safe_text(profile.get('name'))} | {len(target_rows)} | {highest}: {STAGE_LABELS[highest]} |")

    lines.extend(
        [
            "",
            "## Conservative automation rules",
            "",
            "1. Automated records must be interventional and vaccine-relevant.",
            "2. Target matching uses explicit aliases configured in `config/pathogens.json`.",
            "3. Automated stage assignment is based on the highest registered phase and is capped at stage 5.",
            "4. Stage 6 and stage 7 claims require manually curated official or regulatory evidence.",
            "5. Registry records can be incomplete, delayed, duplicated, or differently labelled from publications; inspect every row-level source before operational use.",
            "",
            "## Scope caveat",
            "",
            "This is a vaccine-development landscape, not a disease-incidence map, clinical recommendation, procurement tool, or exhaustive regulatory database. Nationally used products and trials outside ClinicalTrials.gov may be absent.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh the bacterial vaccine-development pipeline.")
    parser.add_argument("--config", default="config/pathogens.json", help="Pathogen configuration JSON")
    parser.add_argument("--seed", default="data/curated_candidates.csv", help="Curated seed CSV")
    parser.add_argument("--out", default="data/pipeline.csv", help="Generated pipeline CSV")
    parser.add_argument("--report", default="reports/automation_summary.md", help="Automation report path")
    parser.add_argument("--no-network", action="store_true", help="Build from curated data only")
    parser.add_argument("--strict-network", action="store_true", help="Fail rather than fall back when API calls fail")
    parser.add_argument("--max-pages", type=int, default=3, help="Maximum pages fetched per query")
    parser.add_argument("--page-size", type=int, default=100, help="API page size (maximum 1000)")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--pause", type=float, default=0.15, help="Pause between API pages")
    args = parser.parse_args(argv)

    profiles = read_json(Path(args.config))
    if not isinstance(profiles, list):
        raise ValueError("Pathogen configuration must be a JSON list")
    curated_rows = [normalize_row(row) for row in read_csv(Path(args.seed))]

    errors: list[str] = []
    query_stats: list[dict[str, Any]] = []
    registry_by_trial: dict[str, dict[str, Any]] = {}

    if not args.no_network:
        for profile in profiles:
            for query in profile.get("clinical_trials_queries", []):
                query = safe_text(query)
                if not query:
                    continue
                try:
                    studies, reported_total = fetch_query(
                        query,
                        max_pages=max(1, args.max_pages),
                        page_size=max(1, min(1000, args.page_size)),
                        timeout=max(1, args.timeout),
                        pause_seconds=max(0.0, args.pause),
                    )
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                    message = f"{safe_text(profile.get('name'))} — query `{query}` failed: {exc}"
                    errors.append(message)
                    if args.strict_network:
                        print(message, file=sys.stderr)
                        return 2
                    query_stats.append(
                        {
                            "pathogen": safe_text(profile.get("name")),
                            "query": query,
                            "reported_total": 0,
                            "retrieved": 0,
                            "accepted": 0,
                        }
                    )
                    continue

                accepted = 0
                for study in studies:
                    primary_blob, full_blob = study_blob(study)
                    if not vaccine_relevant(study, primary_blob, full_blob):
                        continue
                    match, reason = is_target_match(profile, primary_blob, full_blob)
                    if not match:
                        continue
                    row = registry_row(study, profile, reason)
                    trial_id = safe_text(row.get("trial_id")).upper()
                    if not trial_id:
                        continue
                    existing = registry_by_trial.get(trial_id)
                    if existing is None:
                        registry_by_trial[trial_id] = row
                    else:
                        # The same record may match multiple aliases. Keep the first
                        # target assignment and increment the audit count.
                        try:
                            count = int(existing.get("supporting_record_count") or 1)
                        except (TypeError, ValueError):
                            count = 1
                        existing["supporting_record_count"] = count + 1
                    accepted += 1

                query_stats.append(
                    {
                        "pathogen": safe_text(profile.get("name")),
                        "query": query,
                        "reported_total": reported_total,
                        "retrieved": len(studies),
                        "accepted": accepted,
                    }
                )

    rows, merged, added = merge_registry_rows(curated_rows, list(registry_by_trial.values()))
    gap_rows = ensure_gap_rows(rows, profiles)
    rows = sort_rows(rows, profiles)
    write_csv(Path(args.out), rows)
    write_report(
        Path(args.report),
        rows=rows,
        profiles=profiles,
        network_enabled=not args.no_network,
        query_stats=query_stats,
        errors=errors,
        merged=merged,
        added=added,
        gap_rows=gap_rows,
    )

    counts = Counter(safe_text(row.get("pathogen_id")) for row in rows)
    print(f"Wrote {args.out} with {len(rows)} rows")
    print("Rows by pathogen:", ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    if errors:
        print(f"Completed with {len(errors)} network warning(s); curated fallback data were retained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
