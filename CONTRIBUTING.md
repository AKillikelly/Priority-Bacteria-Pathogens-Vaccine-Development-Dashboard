# Contributing

Evidence corrections and implementation improvements are welcome.

## Data contribution standard

A data pull request should:

1. identify the target and candidate clearly;
2. cite a direct, authoritative source;
3. distinguish trial status from programme status;
4. explain any stage change;
5. include a current `last_verified` date;
6. avoid inferring authorization or programme use from trial metadata;
7. pass `python scripts/validate_data.py`.

For substantial changes, describe the search strategy and sources reviewed. Changes to stages 6 or 7 should receive independent subject-matter review.

## Code contribution standard

Keep the site static and dependency-light unless there is a documented need. Test keyboard access, mobile layout, CSV downloads, source links, and GitHub Pages deployment.
