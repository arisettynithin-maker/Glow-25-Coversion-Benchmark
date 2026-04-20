# Deployment — Streamlit Cloud

Step-by-step to get this live on Streamlit Community Cloud.

## Prerequisites
- GitHub account
- Streamlit Community Cloud account (free at share.streamlit.io)
- The processed data file committed to the repo (`data/processed/events_clean.csv`)

## Steps

**1. Push repo to GitHub (public)**
```bash
git init
git config user.name "Nithin Arisetty"
git config user.email "arisettynithin@gmail.com"
git add .
git commit -m "initial commit"
gh repo create glow25-conversion-benchmarker --public --source=. --remote=origin --push
```

**2. Sign in to Streamlit Cloud**
Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.

**3. Create new app**
- Click "New app"
- Select your repository: `glow25-conversion-benchmarker`
- Branch: `main`
- Main file path: `app/streamlit_app.py`

**4. Confirm runtime**
Make sure `runtime.txt` is in the repo root and contains exactly:
```
python-3.11
```

**5. Deploy**
Click "Deploy". First build takes 3–5 minutes while it installs dependencies.

**6. Copy the live URL**
Once deployed, copy the URL (format: `https://yourname-glow25-conversion-benchmarker-app-streamlit-xxxx.streamlit.app`) and paste it into `README.md` under "Live demo".

## Notes
- If the app shows a `FileNotFoundError` for `events_clean.csv`, make sure the processed data file is committed to the repo. The ingest script must be run locally first.
- Streamlit Cloud free tier sleeps apps after inactivity — first load after sleep takes ~30 seconds.
- Secrets (e.g. Kaggle credentials) should go in the Streamlit Cloud "Secrets" section, not hardcoded.
