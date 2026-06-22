# Data dictionary

| Field | Meaning |
|---|---|
| `record_id` | Stable, unique row identifier used by the interface |
| `pathogen_id` | Machine-readable target ID defined in `config/pathogens.json` |
| `pathogen` | Display name |
| `pathogen_group` | Analytical grouping used by a filter |
| `priority_rationale` | Brief reason the target is in scope |
| `target_scope` | Included human-vaccine target definition |
| `candidate` | Candidate, product, programme, or gap-row name |
| `stage_order` | Integer from 0 through 7 |
| `stage` | Generated stage label |
| `status` | Current trial, product, or programme status |
| `status_type` | Clinical candidate, authorization, programme use, or gap-row category |
| `phase` | Registered or curated clinical phase |
| `platform` | Vaccine technology or formulation |
| `sponsor` | Lead sponsor or programme owner reported by the source |
| `trial_id` | ClinicalTrials.gov NCT identifier, when applicable |
| `serovars` | Included serovars, strains, or antigen coverage |
| `population` | Study or intended population |
| `countries` | Study or programme geography |
| `enrollment` | Registered enrollment count |
| `start_date` | Registered study start date |
| `primary_completion_date` | Registered primary completion date |
| `registry_last_updated` | Most recent registry update date |
| `evidence_summary` | Neutral summary of what the cited source supports |
| `next_milestone` | Next observable development milestone |
| `evidence_type` | Provenance category |
| `source_title` | Human-readable citation title |
| `source_url` | Direct evidence URL |
| `source_date` | Publication, registry, or source-update date |
| `last_verified` | Date a curator last checked the claim, `YYYY-MM-DD` |
| `automation_notes` | Matching, refresh, or interpretation caveat |
| `supporting_record_count` | Number of mapped supporting registry signals |
