# Automation summary

Generated: `2026-06-22T18:33:45Z`

## Run status

- Network refresh requested: **no**
- Final rows: **9**
- Curated rows updated from matching registry IDs: **0**
- Newly discovered registry rows added: **0**
- Generated gap rows: **0**

## Rows by pathogen

| Pathogen | Rows | Highest stage |
|---|---:|---|
| Vibrio cholerae | 2 | 7: Programmatic use / stockpile / post-licensure |
| Yersinia pestis | 2 | 4: Phase 2 |
| Shigella spp. | 2 | 4: Phase 2 |
| Klebsiella pneumoniae | 1 | 4: Phase 2 |
| Invasive non-typhoidal Salmonella enterica | 2 | 4: Phase 2 |

## Conservative automation rules

1. Automated records must be interventional and vaccine-relevant.
2. Target matching uses explicit aliases configured in `config/pathogens.json`.
3. Automated stage assignment is based on the highest registered phase and is capped at stage 5.
4. Stage 6 and stage 7 claims require manually curated official or regulatory evidence.
5. Registry records can be incomplete, delayed, duplicated, or differently labelled from publications; inspect every row-level source before operational use.

## Scope caveat

This is a vaccine-development landscape, not a disease-incidence map, clinical recommendation, procurement tool, or exhaustive regulatory database. Nationally used products and trials outside ClinicalTrials.gov may be absent.
