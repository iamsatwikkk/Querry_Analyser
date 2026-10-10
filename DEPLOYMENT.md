# Deployment Guide (GitHub and Vercel)

This guide matches the generated structure: a FastAPI app at `api/index.py` that serves both the API and the `frontend/` files, `requirements.txt` at the repository root, and a minimal `vercel.json`.

Vercel detects FastAPI from `requirements.txt` and runs the `app` object in `api/index.py` as a single function. `vercel.json` adds one rewrite so every path (including `/` and `/api/health`) reaches that app. No build command, output directory or environment variables are needed.

## 1. Create or use the GitHub repository

Create an empty repository named `SQL_QUERRY_ANALYSER` on github.com (no README, no .gitignore, no license, since the project already has them). Use the existing repository if you already created it.

## 2. Push the final project

From the project root (the folder containing `api/`, `src/`, `frontend/`):

```bash
git init
git add .
git commit -m "Final: SQL Query Analyzer and Optimizer"
git branch -M main
git remote add origin https://github.com/<your-username>/SQL_QUERRY_ANALYSER.git
git push -u origin main
```

If the repository already has history, skip `git init`, and use `git remote set-url origin <url>` instead of `git remote add`. GitHub requires a personal access token (not your password) when pushing over HTTPS.

## 3. Sign in to Vercel

Go to vercel.com and choose **Continue with GitHub**.

## 4. Import the repository

Dashboard, then **Add New**, then **Project**, find `SQL_QUERRY_ANALYSER` and click **Import**. If it is missing, click **Adjust GitHub App Permissions** and grant access to that repository.

## 5. Project root

Leave **Root Directory** as `./` (the repository root). The root must be the folder that contains `api/` and `requirements.txt`.

## 6. Build configuration

- Framework Preset: leave as detected (FastAPI or Other)
- Build Command, Output Directory, Install Command: leave empty / default

## 7. Environment variables

None required.

## 8. Deploy

Click **Deploy** and wait for the build to finish. Vercel gives you a URL such as `https://sql-querry-analyser.vercel.app`.

## 9. Test the deployed URL

Open the URL. The analyzer UI should load.

## 10. Check the API

```bash
curl https://<your-deployment>.vercel.app/api/health
curl -X POST https://<your-deployment>.vercel.app/api/analyze -H "Content-Type: application/json" -d '{"query": "SELECT name FROM employee WHERE salary > 50000;"}'
```

Expected: `{"status":"ok"}` and a JSON document with `"valid": true`.

## 11. Check the UI

Click **Analyze Query** on the default query. Overview should show every stage ticked, and the Result tab should list Alice and Charlie. Try the semantic, syntax and lexical error examples from the dropdown.

## 12. Redeploy after a push

Every push to `main` triggers an automatic production deployment:

```bash
git add .
git commit -m "Describe the change"
git push
```

## 13. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `404 NOT_FOUND` on `/` or `/api/health` | `vercel.json` missing or not at the repo root, or Root Directory is not the repo root. Confirm the file is committed. |
| `500` with `ModuleNotFoundError: fastapi` | `requirements.txt` missing at the repo root or not committed. |
| `ModuleNotFoundError: pipeline` or `schema` | `api/index.py` must keep its `sys.path` setup; do not move `api/`, `src/` or `frontend/` apart. |
| UI loads but styling is missing | `frontend/` folder not committed; check `git status` and that `.gitignore` does not exclude it. |
| Tests folder missing on deploy | Expected: `.vercelignore` excludes `tests/` and `docs/` from the deployment. |
| Fonts look different | Inter and JetBrains Mono load from Google Fonts; system fonts are used if blocked. |
| Build used the wrong Python | Vercel uses its default supported Python 3.x; the code uses only standard syntax and runs on 3.9 or newer. |

Note: this project was verified locally (automated tests, a real uvicorn server, and a browser). The Vercel configuration follows Vercel's current FastAPI documentation, but a live Vercel deployment could not be performed from the development sandbox, so run steps 9 to 11 after your first deploy to confirm.
