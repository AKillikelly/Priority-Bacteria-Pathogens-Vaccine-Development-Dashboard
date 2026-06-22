# Start here: publish the dashboard with GitHub Pages

This guide assumes no command-line experience. The safest beginner route is **GitHub Desktop**, because it preserves the hidden `.github/workflows` folder that deploys the site.

## What you already have

- A working static dashboard in `public/index.html`
- Nine source-linked starter records in `data/curated_candidates.csv`
- Pathogen definitions and trial-search terms in `config/pathogens.json`
- A weekly ClinicalTrials.gov refresh script
- Automatic data validation
- A GitHub Pages workflow in `.github/workflows/pages.yml`

## Step 1 — Preview it on your computer

1. Unzip the downloaded project.
2. Open the extracted folder.
3. Open `public`.
4. Double-click `index.html`.

The dashboard works as a standalone page because the data are embedded during the build.

## Step 2 — Create a GitHub account and install GitHub Desktop

1. Create a GitHub account if you do not already have one.
2. Install GitHub Desktop from the official GitHub Desktop site.
3. Sign in to GitHub Desktop.

## Step 3 — Turn the folder into a repository

1. In GitHub Desktop, choose **File → Add local repository**.
2. Select the extracted project folder.
3. GitHub Desktop will say the folder is not yet a Git repository. Select **create a repository here**.
4. Use a clear repository name, for example:
   `priority-bacterial-pathogen-vaccine-dashboard`
5. Keep the default branch as `main`.
6. Create the repository.
7. In the lower-left summary box, enter:
   `Initial dashboard`
8. Select **Commit to main**.

## Step 4 — Publish it to GitHub

1. Select **Publish repository**.
2. Uncheck **Keep this code private** if you want a public Pages site on a free public repository.
3. Select **Publish repository** again.
4. In GitHub Desktop, select **View on GitHub**.

## Step 5 — Enable GitHub Pages

1. On the repository page, select **Settings**.
2. In the left menu, select **Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Open the repository’s **Actions** tab.
5. Select **Refresh and deploy bacterial pathogen dashboard**.
6. If a run failed before Pages was enabled, select the failed run and choose **Re-run all jobs**. You can also choose **Run workflow**.
7. When the deployment job is green, open its published URL.

The URL normally follows this pattern:

```text
https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/
```

## Step 6 — Make the first essential edits

Before treating the dashboard as a research product:

1. Open `data/curated_candidates.csv`.
2. Verify every starter row against its source.
3. Update `last_verified` using `YYYY-MM-DD`.
4. Add, remove, or revise rows as needed.
5. Commit and push the changes. The workflow rebuilds and redeploys automatically.

See [`docs/03_EDIT_DATA.md`](docs/03_EDIT_DATA.md) for the curation rules and stage definitions.

## Step 7 — Share responsibly

Add a named data steward, a review cadence, and a scope statement to your repository. The starter dashboard is a vaccine-development landscape—not a clinical recommendation, procurement tool, incidence tracker, or exhaustive regulatory database.

## Command-line alternative

From inside the extracted project folder:

```bash
git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Then complete **Step 5** above.
