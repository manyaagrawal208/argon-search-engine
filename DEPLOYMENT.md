# Deployment Guide

Running `python app.py` only serves Argon on your own computer, and it stops when you close the terminal. Deploying it gives you a public link that works from any device and network.

## Quick comparison

| Option | Cost | Card needed | Works for Argon | Notes |
|---|---|---|---|---|
| [Hugging Face Spaces](#option-1-hugging-face-spaces-recommended) | Free | No | Yes | Uses the included `Dockerfile`. Link contains your chosen Space name, e.g. `argon`. |
| [Render](#option-2-render) | Free tier | Possibly | Yes | Free apps sleep when idle. Sign-up may ask for a card. |
| [PythonAnywhere (free)](#option-3-pythonanywhere) | Free | No | Probably not | Free accounts can only reach allowlisted sites. |
| [Run locally](#run-locally) | Free | No | Yes | Only on your computer. |

## Run locally

```powershell
# Windows PowerShell
$env:GROQ_API_KEY="your-key-here"
cd path\to\argon-search-engine
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. Set the key **before** running `python app.py`. A key set after the server has started is not picked up.

## Option 1: Hugging Face Spaces (recommended)

Hugging Face Spaces runs Docker apps on a free CPU tier. This repo already contains the `Dockerfile` it needs.

1. **Sign up** at [huggingface.co](https://huggingface.co) (free).
2. **Create a Space:** click your profile picture, then **New Space**.
   - Space name: `argon`
   - SDK: **Docker**, template **Blank**
   - Hardware: **CPU basic (free)**
   - Visibility: **Public**
3. **Upload the files** to the Space (**Files** tab, then **Add file**, then **Upload files**):
   - `app.py`
   - `requirements.txt`
   - `Dockerfile`
   - `.dockerignore`
   - `deploy/huggingface/README.md`, uploaded as **`README.md`** at the top level of the Space. It holds the settings (`sdk: docker`, `app_port: 7860`) that Spaces reads. This is a separate file from the GitHub README and should not replace it.
4. **Add your key as a secret:** Space **Settings**, then **Variables and secrets**, then **New secret**.
   - Name: `GROQ_API_KEY`
   - Value: your Groq key
5. **Wait for the build.** The **App** tab shows the build log, then your app.
6. **Your link** is the Space page, `https://huggingface.co/spaces/<your-username>/argon`. The Space also has a direct app URL, which you can find under the three-dot menu as **Embed this Space**.

Free Spaces may go to sleep after a period of inactivity and wake up on the next visit, which takes a short while.

### Updating the Space

Edit or re-upload the changed file in the Space. It rebuilds automatically.

## Option 2: Render

1. Push this repo to GitHub.
2. On [render.com](https://render.com), choose **New**, then **Web Service**, and connect the repo.
3. Settings:
   - Runtime: **Python**
   - Build command: `pip install -r requirements.txt gunicorn`
   - Start command: `gunicorn app:app`
   - Instance type: **Free**
4. Under **Environment**, add `GROQ_API_KEY`.
5. Deploy. The public URL uses your service name, so naming it `argon` gives you a link containing "argon".

Render may ask for payment details when you sign up, even for the free tier. Free services also spin down when idle and take a moment to wake up.

## Option 3: PythonAnywhere

Free PythonAnywhere accounts can only make outbound connections to an allowlist of sites. DuckDuckGo's domain appears on that list, but:

- Argon also needs to reach the Groq API, and I could not confirm it is on the allowlist.
- The `ddgs` package uses its own HTTP client and may not route through PythonAnywhere's proxy, and in some modes it contacts other search backends that are not allowlisted.

So a free PythonAnywhere account will most likely load the page but fail when you search. Paid accounts have unrestricted internet access. Check the current [allowlist](https://www.pythonanywhere.com/whitelist/) before choosing this option.

If you do use a paid account:

1. In a Bash console: `git clone https://github.com/manyaagrawal208/argon-search-engine.git`
2. In the console: `pip3 install --user -r argon-search-engine/requirements.txt`
3. **Web** tab, **Add a new web app**, **Manual configuration**, matching your Python version.
4. Edit the WSGI file so it contains:

   ```python
   import os, sys
   path = "/home/YOUR_USERNAME/argon-search-engine"
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ["GROQ_API_KEY"] = "your-key-here"   # keep this file private
   from app import app as application
   ```
5. Click **Reload**.

Never commit a WSGI file that contains your key.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | Yes | Authenticates with Groq. Set it as a host secret or in the terminal, never in the code. |
| `PORT` | No | Port to listen on. Default `5000` when running `python app.py`. The Dockerfile binds to 7860. |
| `HOST` | No | Interface to bind to when running `python app.py`. Default `127.0.0.1`. |
| `FLASK_DEBUG` | No | Set to `1` for auto-reload while developing. Leave it off in production. |

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| Page loads but says `GROQ_API_KEY is not set` | The key was not set before the app started. Set it first, then start (or restart) the app. On a host, add it as a secret and restart. |
| `model_not_found` (404) | Your Groq key can't use the model in `MODEL`. List your models with the command in the README and update `MODEL`. |
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt`. |
| Site stops loading after closing the terminal | A local server only runs while its terminal window is open. Deploy it, or start it again. |
| Link works on your PC but not on your phone | `127.0.0.1` means "this computer". Use a deployed link. |
| Search fails on a free host but works locally | The host may block outbound requests. See the PythonAnywhere notes above. |
| `Address already in use` | Another program uses the port. Set a different `PORT`. |
| Rate-limit errors | DuckDuckGo or Groq is throttling you. Wait a bit and try again. |
