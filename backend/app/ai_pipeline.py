import os, json, threading
from .utils import stylize_with_replicate, insert_face_into_template

BASE_TASKS = './tasks'
TEMPLATE_PATH = './templates/template.png'  # default template path

def pipeline(task_id, input_path, uploaded_template_path=None, user_prompt=None):
    task_dir = os.path.join(BASE_TASKS, task_id)
    meta_path = os.path.join(task_dir, 'meta.json')
    def write_meta(m):
        with open(meta_path, 'w') as f:
            json.dump(m, f)

    write_meta({'status': 'processing'})
    try:
        # Stylize the whole uploaded image (don't crop to the face)
        stylized_path = os.path.join(task_dir, 'stylized.png')
        # choose template: prefer uploaded template for this task, otherwise default repository template
        effective_template = None
        if uploaded_template_path and os.path.exists(uploaded_template_path):
            effective_template = uploaded_template_path
        elif os.path.exists(TEMPLATE_PATH):
            effective_template = TEMPLATE_PATH

        # stylize using replicate on the entire input image; pass user prompt if provided
        stylize_with_replicate(input_path, stylized_path, style_reference=effective_template, user_prompt=user_prompt)

        final_path = os.path.join(task_dir, 'final.png')
        # If the user uploaded a template but did not provide a custom prompt,
        # treat the template as a style reference only and return the full stylized image
        # (do not paste into the template). This avoids odd pasted-face results when
        # users expect a full-image stylization to match the template's look.
        if uploaded_template_path and (not user_prompt or str(user_prompt).strip() == ""):
            write_meta({'status': 'done', 'stylized_url': f'/result/{task_id}/stylized.png', 'note': 'used_template_as_style'})
            return

        if effective_template:
            try:
                insert_face_into_template(stylized_path, final_path, effective_template)
                write_meta({'status': 'done', 'result_url': f'/result/{task_id}/final.png'})
            except Exception as e:
                # Insertion failed — return stylized image instead
                write_meta({'status': 'done', 'stylized_url': f'/result/{task_id}/stylized.png', 'note': 'insertion_failed', 'error': str(e)})
        else:
            # No template — return stylized image
            write_meta({'status': 'done', 'stylized_url': f'/result/{task_id}/stylized.png', 'note': 'no_template'})
    except Exception as e:
        write_meta({'status': 'error', 'error': str(e)})

def start_pipeline_async(task_id, input_path, uploaded_template_path=None, user_prompt=None):
    t = threading.Thread(target=pipeline, args=(task_id, input_path, uploaded_template_path, user_prompt), daemon=True)
    t.start()
