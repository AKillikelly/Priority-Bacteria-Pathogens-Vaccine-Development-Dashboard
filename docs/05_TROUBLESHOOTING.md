# Troubleshooting

## The site returns 404

- Confirm **Settings → Pages → Source** is **GitHub Actions**.
- Confirm the repository contains `.github/workflows/pages.yml`.
- Confirm the default branch is `main` or update the workflow trigger.
- Open **Actions** and inspect both the `build` and `deploy` jobs.
- Use the exact deployment URL shown by the successful workflow.

## No workflow appears in the Actions tab

The hidden `.github` directory was probably omitted during upload. Use GitHub Desktop, or verify that this exact path exists in the repository:

```text
.github/workflows/pages.yml
```

## The build fails on data validation

Read the error line in the Actions log. Typical causes are:

- duplicate `record_id`
- `pathogen_id` not present in `config/pathogens.json`
- `stage_order` outside 0–7
- missing or malformed source URL
- malformed `last_verified` date
- invalid NCT identifier
- a comma that broke CSV column alignment

Run locally:

```bash
python scripts/fetch_pipeline.py --no-network
python scripts/validate_data.py
```

## The ClinicalTrials.gov refresh warns or times out

The standard workflow falls back to curated records. Check `public/automation_summary.md` or the deployed **Automation report** link. Re-run the workflow later and verify time-sensitive registry statuses manually.

## A relevant trial is missing

1. Search the registry manually.
2. Add candidate aliases to `match_terms`.
3. Add a targeted query to `clinical_trials_queries`.
4. Check whether an `exclude_terms` value is too broad.
5. Add a curated row when the programme is outside ClinicalTrials.gov.

## An irrelevant trial appears

Add a precise exclusion term, strengthen target-specific matching, or add a curated correction. Do not use overly broad exclusions that could hide valid comparator or combination-vaccine studies.

## Changes are not visible

- Confirm the newest workflow completed successfully.
- Hard-refresh the browser.
- Verify you edited `data/curated_candidates.csv` or the template—not only a generated local file.
- Confirm you pushed the commit to `main`.

## The page opens locally but downloads do not work

Rebuild the output so the CSV and report are copied into `public/`:

```bash
python scripts/build_dashboard.py
```

Then open the page through a local server:

```bash
python -m http.server 8000 --directory public
```
