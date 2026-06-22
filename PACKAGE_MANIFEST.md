# Package manifest

## Publishable output

- `public/index.html` — self-contained dashboard page
- `public/bacterial_vaccine_development_pipeline_data.csv` — downloadable merged dataset
- `public/automation_summary.md` — build audit
- `public/pathogens.json` — published target configuration
- `public/.nojekyll` — disables Jekyll processing for the artifact

## Curated inputs

- `data/curated_candidates.csv` — source-linked manual records
- `config/pathogens.json` — pathogen metadata, search terms, and exclusions

## Build and quality scripts

- `scripts/fetch_pipeline.py` — ClinicalTrials.gov API refresh and merge
- `scripts/validate_data.py` — schema and quality validation
- `scripts/build_dashboard.py` — static-site builder
- `scripts/dashboard_template.html` — interface template

## GitHub automation

- `.github/workflows/pages.yml` — scheduled refresh and GitHub Pages deployment

## Guidance

- `START_HERE.md`
- `README.md`
- `CONTRIBUTING.md`
- `docs/00_QUICK_CHECKLIST.md`
- `docs/01_PUBLISH_WITH_GITHUB_DESKTOP.md`
- `docs/02_PUBLISH_WITH_TERMINAL.md`
- `docs/03_EDIT_DATA.md`
- `docs/04_AUTOMATION.md`
- `docs/05_TROUBLESHOOTING.md`
- `docs/DATA_DICTIONARY.md`
- `docs/dashboard-preview.png`

## Legal and citation

- `LICENSE`
- `CITATION.cff`
