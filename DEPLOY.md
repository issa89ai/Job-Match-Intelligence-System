# Deployment Guide — Render (API) + Streamlit Cloud (UI)

This app has two parts:
- **Backend** — FastAPI, deployed on [Render](https://render.com)
- **Frontend** — Streamlit, deployed on [Streamlit Community Cloud](https://streamlit.io/cloud)

---

## Step 1 — Push your code to GitHub

If you haven't already:

```bash
cd "Job Match Intelligence System"
git init
git add .
git commit -m "Initial commit"
```

Then create a new repo on [github.com](https://github.com/new) and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

> ⚠️ Make sure `.streamlit/secrets.toml` is NOT committed — it's already in `.gitignore`.

---

## Step 2 — Deploy the FastAPI backend on Render

1. Go to [render.com](https://render.com) and sign up / log in.
2. Click **New → Web Service**.
3. Connect your GitHub account and select your repo.
4. Render will detect `render.yaml` automatically. Confirm these settings:
   - **Name:** `job-match-api` (or anything you like)
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements-backend.txt`
   - **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
5. Click **Advanced** → **Add Environment Variable** and add each of these:

   | Key | Value |
   |-----|-------|
   | `JSEARCH_API_KEY` | `42c92c90a9mshba9c2eef84e2989p1562f1jsne532c9b4ccd9` |
   | `SMTP_HOST` | `smtp.gmail.com` |
   | `SMTP_PORT` | `587` |
   | `SMTP_SENDER_EMAIL` | `issa89.ai@gmail.com` |
   | `SMTP_SENDER_PASSWORD` | `qfwe vjzp hkuo cixr` |
   | `APP_BASE_URL` | *(leave blank for now — fill in after Step 3)* |
   | `ALLOWED_ORIGINS` | *(leave blank for now — fill in after Step 3)* |

6. Click **Create Web Service**. Render will build and deploy (~3 minutes).
7. Once it's live, copy your Render URL — it looks like:
   ```
   https://job-match-api.onrender.com
   ```
   You'll need this in the next step.

> 💡 **Free tier note:** On Render's free plan the service spins down after 15 minutes of inactivity. The first request after that takes ~30 seconds to wake up. This is normal — upgrade to the $7/month plan if you want it always-on.

---

## Step 3 — Deploy the Streamlit frontend on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your repository, branch `main`, and set the **Main file path** to:
   ```
   app/streamlit_app.py
   ```
4. Under **Advanced settings → Secrets**, paste exactly this (replacing the URL with your Render URL from Step 2):
   ```toml
   API_URL = "https://job-match-api.onrender.com"
   ```
5. Click **Deploy**. Streamlit will install `requirements-frontend.txt` and launch (~2 minutes).
6. Once live, copy your Streamlit URL — it looks like:
   ```
   https://yourname-job-match.streamlit.app
   ```

---

## Step 4 — Wire the two services together

Go back to your **Render dashboard → job-match-api → Environment**:

1. Set `APP_BASE_URL` to your Streamlit URL:
   ```
   https://yourname-job-match.streamlit.app
   ```
2. Set `ALLOWED_ORIGINS` to your Streamlit URL:
   ```
   https://yourname-job-match.streamlit.app
   ```
3. Click **Save Changes**. Render will redeploy automatically (~1 minute).

---

## Step 5 — Test it

Open your Streamlit URL in the browser. You should see the app load with the dark theme.

- **Register** a new account in the sidebar.
- **Create a profile**, fill in your skills and experience.
- Go to the **Job Matches** tab and run a live search.

If you see a connection error, check that the Render service is awake (visit your Render URL directly — `https://job-match-api.onrender.com/docs` should show the API docs).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Connection refused" in Streamlit | Render service is sleeping — open `your-render-url/docs` to wake it, then retry |
| "JSearch API key missing" | Check `JSEARCH_API_KEY` env var is set in Render dashboard |
| Password reset emails not sending | Check `SMTP_SENDER_EMAIL` and `SMTP_SENDER_PASSWORD` in Render |
| Data resets after redeploy | Free Render plan has an ephemeral disk — upgrade to paid for persistence |
| Streamlit shows blank page | Check the **Logs** tab in Streamlit Cloud for import errors |

---

## Local development (unchanged)

```bash
# Terminal 1 — backend
uvicorn src.api.main:app --reload

# Terminal 2 — frontend
streamlit run app/streamlit_app.py
```

The app auto-detects localhost when no `API_URL` secret is set.
