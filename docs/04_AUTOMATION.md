# Automation and deployment

## Workflow triggers

`.github/workflows/pages.yml` runs:

- on every push to `main`
- when manually started from the Actions tab
- every Monday at 06:17 UTC

## Build sequence

1. Check out the repository.
2. Set up Python 3.12.
3. Query ClinicalTrials.gov API v2.
4. Merge registry results with curated records.
5. Validate the generated CSV.
6. Build `public/index.html` and downloadable artifacts.
7. Upload the `public/` folder as a Pages artifact.
8. Deploy the artifact to GitHub Pages.

## Registry query controls

Target queries and aliases live in `config/pathogens.json`. The default script options are:

```text
--max-pages 3
--page-size 100
--timeout 30
--pause 0.15
```

Run `python scripts/fetch_pipeline.py --help` for all options.

## Failure behavior

Without `--strict-network`, a ClinicalTrials.gov network or JSON error is recorded as a warning and the build keeps the curated fallback data. This protects site availability but means the published registry status may not be refreshed during that run. Review `automation_summary.md` after every important release.

Use `--strict-network` in a separate quality-control job when a failed refresh must block release.

## Matching safeguards

- Only interventional, vaccine-relevant records are accepted.
- Target terms must appear in configured fields.
- *K. pneumoniae* logic rejects “pneumoniae” ambiguity without “Klebsiella.”
- iNTS logic requires non-typhoidal, Enteritidis, Typhimurium, or iNTS markers.
- Veterinary-only plague records can be excluded by configured terms.
- Automated stage assignment is capped at stage 5.

No text-matching system eliminates all false positives or false negatives. Human review is mandatory.

## Workflow security

The workflow requests only the permissions needed to read repository content and deploy Pages. It does not use a personal access token, commit generated files, or accept untrusted script input from site visitors.
