# Edit and curate the data

The authoritative manual input is `data/curated_candidates.csv`. Do not hand-edit `public/index.html`; it is generated.

## Stage model

| Stage | Label | Typical evidence |
|---:|---|---|
| 0 | Evidence gap | No mapped human-vaccine pathway in the configured dataset |
| 1 | Discovery / translational | Named programme with source-backed discovery activity |
| 2 | Preclinical / manufacturing-enabling | Source-backed preclinical, toxicology, process, or manufacturing-enabling work |
| 3 | Phase 1 | Registered or reliably sourced early human study |
| 4 | Phase 2 | Registered dose, schedule, age-de-escalation, or expanded safety/immunogenicity study |
| 5 | Efficacy / Phase 3 | Efficacy-stage or Phase 3 programme |
| 6 | Authorization / WHO prequalification | Current official regulatory authorization or WHO prequalification evidence |
| 7 | Programmatic use / stockpile / post-licensure | Current official programme, stockpile, routine-use, or mature post-licensure pathway evidence |

**Hard rule:** automated registry matching can assign stages 3–5 but cannot create stages 6 or 7.

## Add a row

1. Copy an existing row with the same general evidence type.
2. Create a stable, unique `record_id`, such as `curated-shigella-candidate-year`.
3. Use one of the exact `pathogen_id` values from `config/pathogens.json`.
4. Enter a concise candidate name and source-backed stage.
5. Distinguish trial status from programme status.
6. Add trial ID, sponsor, population, country, serovars, and platform when supported.
7. Write a neutral evidence summary that does not overstate the source.
8. State the next observable milestone.
9. Add source title, source URL, source date, and `last_verified` date.
10. Run validation and inspect the rebuilt dashboard.

## CSV editing cautions

CSV fields containing commas must remain quoted. A spreadsheet editor can help, but save as UTF-8 CSV and verify that headers are unchanged. The safest pattern is to preserve the existing column order.

## Evidence-type guidance

Use specific labels, for example:

- `Curated official source`
- `Curated trial registry`
- `Curated peer-reviewed evidence`
- `Curated sponsor source`
- `Automated ClinicalTrials.gov`

Do not describe sponsor statements as regulatory evidence. Do not infer approval from a Phase 4 label, completed trial, emergency stockpile contract, or publication alone.

## Update a ClinicalTrials.gov row

Place the NCT number in `trial_id`. During a connected build, `fetch_pipeline.py` can update:

- status
- registered phase
- countries
- enrollment
- study start date
- primary completion date
- registry last-update date

The curated evidence narrative and stage 6–7 claims remain under manual control.

## Remove or archive a row

Deleting a row removes it from the next build. For reproducible research, consider preserving historical datasets through tagged GitHub releases rather than silently overwriting an analytical snapshot.

## Validate before committing

```bash
python scripts/fetch_pipeline.py --no-network
python scripts/validate_data.py
python scripts/build_dashboard.py
```
