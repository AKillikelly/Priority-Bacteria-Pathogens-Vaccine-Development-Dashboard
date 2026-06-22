# Publish with Git and the terminal

## Prerequisites

- Git installed
- A GitHub account
- An empty GitHub repository already created

## Initialize and push

Run these commands from the project root:

```bash
git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## Enable Pages

1. In GitHub, open **Settings → Pages**.
2. Set **Source** to **GitHub Actions**.
3. Open **Actions → Refresh and deploy bacterial pathogen dashboard**.
4. Run or re-run the workflow.

## Local development

Build using curated data only:

```bash
python scripts/fetch_pipeline.py --no-network
python scripts/validate_data.py
python scripts/build_dashboard.py
python -m http.server 8000 --directory public
```

Build with the live registry refresh:

```bash
python scripts/fetch_pipeline.py
python scripts/validate_data.py
python scripts/build_dashboard.py
```

## Push an update

```bash
git add .
git commit -m "Describe the evidence update"
git push
```
