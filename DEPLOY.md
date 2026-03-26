# Deploy CAIT (Render API + Streamlit Cloud)

You run **two** free services: the API on **Render**, the UI on **Streamlit Community Cloud**.

## 1. Push the repo to GitHub

Render and Streamlit Cloud both deploy from a GitHub repository.

## 2. Deploy the FastAPI backend on Render

### Option A — Blueprint (recommended)

1. In [Render Dashboard](https://dashboard.render.com): **New** → **Blueprint**.
2. Connect the repo that contains `render.yaml`.
3. Apply the blueprint. Wait until the web service is **Live**.

### Option B — Manual Web Service

1. **New** → **Web Service** → connect the same repo.
2. **Runtime:** Python 3.
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Instance type:** Free.
6. Create the service and wait for a successful deploy.

### After Render finishes

- Open your service URL, e.g. `https://cait-api.onrender.com`.
- Check `https://<your-service>.onrender.com/health` — you should see `{"status":"ok"}`.

**Note (free tier):** The service **spins down** after idle time; the first request after that can take **~1 minute**. SQLite data on the free instance may not survive all redeploys; use this stack for demos unless you add a hosted database.

## 3. Deploy Streamlit on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → pick the **same repo** and branch.
3. **Main file path:** `streamlit_app.py` (repo root).
4. **App URL** (advanced): optional custom subdomain on `streamlit.app`.

### Secrets (required)

**Settings** (gear on the app) → **Secrets**, add:

```toml
CAIT_API_URL = "https://YOUR-SERVICE-NAME.onrender.com"
```

Use your **exact** Render HTTPS base URL: **no trailing slash**.

Save and **Reboot** the app from the menu.

## 4. Smoke test

1. Open the `*.streamlit.app` URL.
2. Sidebar → **API base URL** should default from secrets; if not, paste your Render URL.
3. **Team** → add a member → **Tasks** → create a task → **Dashboard** should show data.

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| Streamlit shows connection errors | Render URL in secrets, `https://`, no trailing slash; Render service is not sleeping (retry after ~1 min). |
| CORS errors in browser | Unusual for this app (Streamlit calls the API from the server). If you add a browser client, ensure API CORS includes your origin. |
| Import errors on Render | `requirements.txt` at repo root; `app` package present. |

## Security (production)

The API exposes `POST /reset` (wipes all data). For a public deployment, consider removing or protecting that route in `app/routers/reset.py` and `app/main.py`.
