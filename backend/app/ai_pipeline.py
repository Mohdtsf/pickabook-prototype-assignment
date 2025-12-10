import os, json, threading
from .utils import stylize_with_replicate, insert_face_into_template

BASE_TASKS = './tasks'
TEMPLATE_PATH = './templates/template.png'  # expected template path

def pipeline(task_id, input_path):
    task_dir = os.path.join(BASE_TASKS, task_id)
    meta_path = os.path.join(task_dir, 'meta.json')
    def write_meta(m):
        with open(meta_path, 'w') as f:
            json.dump(m, f)

    write_meta({'status': 'processing'})
    try:
        # For this variant, stylize the whole uploaded image (don't crop to the face)
        stylized_path = os.path.join(task_dir, 'stylized.png')
        # stylize using replicate on the entire input image
        stylize_with_replicate(input_path, stylized_path, style_reference=TEMPLATE_PATH)

        # Try to auto-insert into template if template exists. If not, return stylized image.
        final_path = os.path.join(task_dir, 'final.png')
        if os.path.exists(TEMPLATE_PATH):
            try:
                insert_face_into_template(stylized_path, final_path, TEMPLATE_PATH)
                write_meta({'status': 'done', 'result_url': f'/result/{task_id}/final.png'})
            except Exception as e:
                # If insertion fails for any reason, return the stylized image instead
                write_meta({'status': 'done', 'stylized_url': f'/result/{task_id}/stylized.png', 'note': 'insertion_failed', 'error': str(e)})
        else:
            # Template missing — return stylized image so frontend can show something
            write_meta({'status': 'done', 'stylized_url': f'/result/{task_id}/stylized.png', 'note': 'template_missing'})
    except Exception as e:
        write_meta({'status': 'error', 'error': str(e)})

def start_pipeline_async(task_id, input_path):
    t = threading.Thread(target=pipeline, args=(task_id, input_path), daemon=True)
    t.start()
