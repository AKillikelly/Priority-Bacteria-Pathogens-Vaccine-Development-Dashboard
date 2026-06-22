# Publish with GitHub Desktop

This is the recommended route for a first deployment.

## 1. Unzip the project

Keep all folders together. The hidden `.github/workflows/pages.yml` file is essential because it tells GitHub how to build and deploy the site.

## 2. Create the local Git repository

1. Open GitHub Desktop.
2. Select **File → Add local repository**.
3. Choose the extracted project folder.
4. When prompted, choose **create a repository here**.
5. Use `main` as the default branch.
6. Create the repository.
7. Enter `Initial dashboard` as the commit summary.
8. Select **Commit to main**.

## 3. Publish to GitHub

1. Select **Publish repository**.
2. Choose the repository name.
3. For a public site, uncheck **Keep this code private**.
4. Select **Publish repository**.
5. Select **View on GitHub**.

## 4. Enable Pages deployment

1. Open **Settings → Pages** in the GitHub repository.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. Open **Actions**.
4. Select **Refresh and deploy bacterial pathogen dashboard**.
5. Choose **Run workflow**, or re-run the initial job if it began before Pages was enabled.
6. Wait for both `build` and `deploy` to display green check marks.
7. Open the deployment URL shown on the workflow summary.

## 5. Publish future changes

1. Edit files locally.
2. Return to GitHub Desktop.
3. Review the changed-file list.
4. Enter a meaningful commit summary, such as `Verify Shigella candidate status`.
5. Select **Commit to main**.
6. Select **Push origin**.

Every push to `main` triggers validation, rebuilding, and deployment.

## Suggested safer team workflow

For a multi-person project, protect `main` and use branches plus pull requests. Require at least one reviewer for source-data changes, especially stage 6 and 7 claims.
