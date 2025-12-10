# Pickabook-proto

Prototype: user uploads a child's photo -> face detected & cropped -> stylized via Replicate img2img -> pasted into a provided illustration template -> result served for download.

Repo layout

pickabook-prototype/
├─ frontend/ # Next.js + Tailwind app
├─ backend/ # FastAPI app
│ ├─ app/
│ │ ├─ main.py
│ │ ├─ ai_pipeline.py
│ │ └─ utils.py
│ ├─ requirements.txt
│ └─ Dockerfile
├─ templates/ # place your template.png here
├─ architecture.png # simple diagram placeholder
└─ README.md

Quickstart (Windows PowerShell)

1. Backend: create venv and install dependencies

PowerShell commands (run from the backend folder):
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

2. Put your template illustration into templates/template.png.

3. Set environment variables for the session (PowerShell):
   $env:REPLICATE_API_TOKEN = "your_replicate_token_here"
  $env:NEXT_PUBLIC_BACKEND_URL = "http://localhost:8000"

4. Run backend locally (from backend folder):
   uvicorn app.main:app --reload --port 8000

5. Frontend: install and run (from frontend folder):
   npm install
   npm run dev

# open http://localhost:3000

Notes

- This prototype uses MediaPipe for face detection, Replicate for managed img2img stylization, and Pillow/OpenCV to insert the stylized face into the template.
- Set REPLICATE_API_TOKEN to use the Replicate client. Update the model id in backend/app/utils.py to target a specific replicate model and adapt inputs if required by that model's API.

## Environment (.env) files

- Backend: you can create a `.env` file in the repository root (or set environment variables directly). Typical values:

  REPLICATE_API_TOKEN="<your_replicate_api_token>"

  # Optional: override the template path (default is ./templates/template.png)

  TEMPLATE_PATH="./templates/template.png"

  Place the `.env` file in the repo root (one level above `backend/`) so the backend loads it when starting via `uvicorn` (the backend code attempts to load `../.env`).

- Frontend: create a `.env.local` (Next.js convention) inside the `frontend/` folder and add:

  NEXT_PUBLIC_BACKEND_URL="http://localhost:8000"

  This exposes the backend base URL to the client. You can also set this value in your shell when running the dev server.

## Using a different Replicate model

The backend currently calls a Replicate img2img-style model inside `backend/app/utils.py` in the function `stylize_with_replicate()`.

- To change the model: open `backend/app/utils.py` and locate the `MODEL = "black-forest-labs/flux-kontext-pro"` line — replace it with the model id you want to use.
- Some models expect different input keys or formats (for example they may accept an image URL instead of a base64 data URI, or use different parameter names). In that same function you will find the `inputs = {...}` dictionary — update keys and values to match the chosen model's API.
- When switching models, carefully review the model's docs on Replicate (or the provider) for required input keys and expected output format. The helper `_extract_url()` in `utils.py` tries to handle several output shapes, but you may need to adapt it for unusual return types.

## Template and placement notes

- Put your illustration template at `templates/template.png`. The pipeline attempts to auto-insert the stylized face into that file when present. If the file is missing, the pipeline will return the stylized face PNG as the result so you still get an output.
- The compositing logic is in `backend/app/utils.py` (`insert_face_into_template()`); tweak the sizing/padding constants there if your template's placeholder region needs different alignment.

What to tune

- Coordinates & sizing used in insert_face_into_template() are example values — adjust them to match your illustration placeholder.
- If the chosen Replicate model requires a different input format (URL vs base64), update stylize_with_replicate() accordingly.
