from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from uuid import uuid4
import os, shutil, json

# Load .env (if present) so env vars like REPLICATE_API_TOKEN are available
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)
except Exception:
    # python-dotenv may not be installed (devs can set env vars manually)
    pass

# import pipeline after loading env so REPLICATE_API_TOKEN in utils is picked up
from .ai_pipeline import start_pipeline_async

app = FastAPI()
# Configure CORS origins via environment for deployed frontend(s).
# Accepts a comma-separated list in ALLOW_ORIGINS or FRONTEND_URLS.
allowed = os.getenv('ALLOW_ORIGINS') or os.getenv('FRONTEND_URLS')
if allowed:
    origins = [o.strip() for o in allowed.split(',') if o.strip()]
else:
    # default: local development
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_TASKS = './tasks'
os.makedirs(BASE_TASKS, exist_ok=True)

# Ensure template path exists: some repos have 'template.png.png' by accident.
template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
template_png = os.path.join(template_dir, 'template.png')
template_png_dup = os.path.join(template_dir, 'template.png.png')
if not os.path.exists(template_png) and os.path.exists(template_png_dup):
    try:
        shutil.copyfile(template_png_dup, template_png)
        print(f"Copied {template_png_dup} -> {template_png}")
    except Exception as e:
        print(f"Failed to copy template file: {e}")

@app.post('/upload')
async def upload(photo: UploadFile = File(...), template: UploadFile = File(None), prompt: str = Form(None)):
    task_id = str(uuid4())
    task_dir = os.path.join(BASE_TASKS, task_id)
    os.makedirs(task_dir, exist_ok=True)
    input_path = os.path.join(task_dir, 'input.jpg')
    with open(input_path, 'wb') as f:
        shutil.copyfileobj(photo.file, f)

    # optional template uploaded by user
    template_path = None
    if template is not None:
        template_path = os.path.join(task_dir, 'template.png')
        with open(template_path, 'wb') as tf:
            shutil.copyfileobj(template.file, tf)

    # Require that the user provides either a template file or a prompt
    if template_path is None and (prompt is None or str(prompt).strip() == ""):
        return JSONResponse({'error': 'Please provide either a template image or a custom prompt.'}, status_code=400)
    meta = {'status': 'queued'}
    with open(os.path.join(task_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f)
    # start pipeline with optional template and prompt
    start_pipeline_async(task_id, input_path, template_path, prompt)
    return {'task_id': task_id}

@app.get('/status/{task_id}')
async def status(task_id: str):
    meta_path = os.path.join(BASE_TASKS, task_id, 'meta.json')
    if not os.path.exists(meta_path):
        return JSONResponse({'status': 'not_found'}, status_code=404)
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    return meta

@app.get('/result/{task_id}/final.png')
async def result_image(task_id: str):
    # legacy specific route — redirect to generic handler
    path = os.path.join(BASE_TASKS, task_id, 'final.png')
    if not os.path.exists(path):
        return JSONResponse({'status': 'not_ready'}, status_code=404)
    return FileResponse(path, media_type='image/png')


@app.get('/result/{task_id}/{filename}')
async def result_file(task_id: str, filename: str):
    # allow only specific filenames for safety
    allowed = {'final.png', 'stylized.png'}
    if filename not in allowed:
        return JSONResponse({'status': 'forbidden'}, status_code=403)
    path = os.path.join(BASE_TASKS, task_id, filename)
    if not os.path.exists(path):
        return JSONResponse({'status': 'not_ready'}, status_code=404)
    return FileResponse(path, media_type='image/png')


# Manual placement endpoint removed — pipeline now auto-inserts into template when possible.
