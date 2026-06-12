# Solar Analyzer

A solar PV analyzer and monitoring dashboard.

## Run locally

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Optional: set `GEMINI_API_KEY` in your environment or Streamlit secrets if you want the "Analyze with AI" button to return Gemini optimization tips.

## Deploy via GitHub + Streamlit Cloud

1. Commit and push this repo to GitHub.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Create a new app and select this repository.
4. Set the main file to `app.py`.
5. Streamlit Cloud will install `requirements.txt` and deploy the app.

Once deployed, you will get a public URL you can share with anyone.
