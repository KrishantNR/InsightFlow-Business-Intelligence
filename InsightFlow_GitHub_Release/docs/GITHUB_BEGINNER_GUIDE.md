# Publish InsightFlow on GitHub — Beginner Guide

This guide uses GitHub Desktop so you do not need to learn Git commands first.

## Before you publish

1. Extract the release ZIP into a permanent folder, for example `Documents\InsightFlow`.
2. Open that folder and confirm that `app.py`, `requirements.txt`, `README.md`, `START_INSIGHTFLOW.bat`, `data`, `docs`, `.github` and `.gitignore` are present.
3. Never place your actual OpenAI API key in any file in this folder. Do not include `.env`, `.streamlit/secrets.toml`, private company data, browser exports or virtual environments.
4. Run `START_INSIGHTFLOW.bat` locally and confirm the app opens. Keep the QA report and screenshots of your real test runs for your capstone evidence.

## Publish with GitHub Desktop

1. Create/sign in to your account at [GitHub](https://github.com/).
2. Install [GitHub Desktop](https://desktop.github.com/) and sign in to the same account.
3. In GitHub Desktop choose **File → Add Local Repository** and browse to the extracted `InsightFlow` folder.
4. If GitHub Desktop says the folder is not a Git repository, use its **create a repository** option for that same folder. Do not create a nested second `InsightFlow` folder by accident.
5. Use repository name `InsightFlow` (or `InsightFlow-Business-Intelligence`), description `Evidence-grounded business intelligence and conversational analytics capstone prototype`, and choose the `main` branch.
6. Review the list of changed files. Make sure no `.env`, `.streamlit/secrets.toml`, API key, `.venv`, `__pycache__`, `.pytest_cache`, or private data appears.
7. Enter a commit summary such as `Prepare initial InsightFlow capstone release`, then click **Commit to main**.
8. Click **Publish repository**. For a portfolio repository, choose **Public** only after checking the files and confirming your university permits public source-code release. If uncertain, publish as **Private** first and switch it to Public after review.
9. Open the repository on GitHub.com and confirm the README renders, the file list is correct and the `Actions` tab shows the quality workflow.

GitHub's official walkthrough: [Add an existing project using GitHub Desktop](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-an-existing-project-to-github-using-github-desktop).

## After publishing: turn on repository protection

Open the repository on GitHub.com → **Settings → Code security and analysis** (the label may vary slightly by UI version). Enable:

- Dependabot alerts.
- Secret scanning.
- Push protection, where available.
- Code scanning/default setup, where available for your repository/account.

This project includes Dependabot configuration and a lightweight local secret-pattern scan, but those do not replace GitHub's platform security features. See [GitHub repository security settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository) and [push protection setup](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/prevent-future-leaks/enable-push-protection).

## How to update the project later

1. Make a small change in your local project folder.
2. Run the project tests (see README).
3. Open GitHub Desktop; it will show changed files.
4. Review the diff. Write a clear commit summary, for example `Add grouped margin analysis`.
5. Click **Commit to main**, then **Push origin**.
6. Open GitHub's Actions tab and confirm the quality workflow passes.

## Host the live application

Use [Streamlit Community Cloud](https://share.streamlit.io/) for the simplest public demo:

1. Sign in to Community Cloud with GitHub.
2. Choose **Create app**.
3. Select the `InsightFlow` repository, the `main` branch and `app.py` as the entrypoint path.
4. In Advanced settings, select Python 3.12 (the Community Cloud default documented currently) and deploy.
5. Community Cloud provides an `*.streamlit.app` URL. Add that URL and your GitHub repository URL to your resume.

Official guide: [Deploy an app on Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

### Important public-demo API-key rule

Do **not** paste your personal API key into the Streamlit Cloud Secrets field for a public, unauthenticated app. If the app uses a shared key, visitors may trigger requests that are billed to your account. Leave the shared key unset so the demo defaults to local analytical mode and each visitor can choose whether to enter their own key into the session-only input. A production public service needs authentication, per-user identity, server-side quotas, abuse monitoring and appropriate privacy controls first.

Streamlit's official [secrets management guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) explains how to store secrets outside Git. This repository's `.gitignore` excludes `.streamlit/secrets.toml`.

## Add it to your resume

Use both links:

- **Live Demo:** your `https://...streamlit.app` URL.
- **GitHub:** your repository URL.

If the LLM mode is not enabled on the public demo, say “LLM-assisted analysis available with user-supplied API key” rather than implying the hosted application uses your private key. Do not claim production security or arbitrary autonomous SQL execution.
