import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import requests
import base64
import mediapipe as mp
import replicate


REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

# ---------------------------------------------------------
# 1) FACE DETECTION + CROP (keep the same)
# ---------------------------------------------------------
def detect_and_crop_face(input_path: str, out_path: str):
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError('cannot read input image')
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    mp_face = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
    results = mp_face.process(img_rgb)
    if not results.detections:
        raise ValueError('no face detected')

    h, w, _ = img.shape
    best = None
    best_area = 0
    for det in results.detections:
        bbox = det.location_data.relative_bounding_box
        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        bw = int(bbox.width * w)
        bh = int(bbox.height * h)
        area = bw * bh
        if area > best_area:
            best = (x, y, bw, bh)
            best_area = area

    x, y, bw, bh = best
    pad = int(0.25 * max(bw, bh))
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(w, x + bw + pad)
    y1 = min(h, y + bh + pad)

    crop = img_rgb[y0:y1, x0:x1]
    out = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    cv2.imwrite(out_path, out)

# ---------------------------------------------------------
# 2) STYLIZATION — FREE MODEL: flux-kontext-pro
# ---------------------------------------------------------
def stylize_with_replicate(input_face_path: str, out_path: str, style_reference: str = None):
    """
    FREE-QUOTA MODEL: black-forest-labs/flux-kontext-pro
    This model supports image editing and works well enough for assignment testing.
    """

    if REPLICATE_API_TOKEN is None:
        raise ValueError("REPLICATE_API_TOKEN is not set")

    MODEL = "black-forest-labs/flux-kontext-pro"

    # read cropped face
    with open(input_face_path, "rb") as f:
        img_bytes = f.read()

    # children-book style prompt
    prompt = (
        "Transform this child's face into a soft children's-book illustration style. "
        "Pastel colors, clean outlines, gentle shading, warm expression, stylized but "
        "identity-preserving illustration."
    )

    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    # send image as base64 data URI to avoid sending raw bytes in JSON
    data_uri = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")
    # Use the model's expected input key and request PNG output
    inputs = {
        "input_image": data_uri,
        "prompt": prompt,
        "output_format": "png",
    }

    print(f"Calling FREE model {MODEL} ...")
    try:
        output = client.run(MODEL, input=inputs)
    except Exception as exc:
        # include full traceback for easier debugging
        import traceback
        tb = traceback.format_exc()
        raise RuntimeError(f"Replicate call failed: {exc}\n{tb}")

    if not output:
        raise RuntimeError("Replicate returned no output.")

    # Try to extract a URL from the output. Replicate client may return
    # a string, a list/tuple, a dict, or a FileOutput-like object.
    def _extract_url(obj):
        # string
        if isinstance(obj, str):
            return obj
        # dict-like
        if isinstance(obj, dict):
            for k in ("url", "output", "image", "file", "result"):
                v = obj.get(k)
                if isinstance(v, str) and v.startswith("http"):
                    return v
        # list/tuple: try first element
        if isinstance(obj, (list, tuple)) and len(obj) > 0:
            return _extract_url(obj[0])
        # object with attributes (FileOutput)
        for attr in ("url", "get", "download_url", "uri"):
            if hasattr(obj, attr):
                try:
                    val = getattr(obj, attr)
                    # if callable, call it
                    if callable(val):
                        val = val()
                except Exception:
                    val = None
                if isinstance(val, str) and val.startswith("http"):
                    return val
                # sometimes val can be a list/dict
                if isinstance(val, (list, tuple, dict)):
                    res = _extract_url(val)
                    if res:
                        return res
        # fallback to string representation if it looks like a URL
        s = str(obj)
        if s.startswith("http"):
            return s
        return None

    out_url = _extract_url(output)
    if out_url is None:
        # write debug dump so we can inspect the unexpected response type
        debug_path = out_path + ".replicate-debug.txt"
        with open(debug_path, "w", encoding="utf-8") as df:
            df.write("REPULATE OUTPUT DUMP:\n")
            try:
                df.write(str(output))
            except Exception:
                df.write(repr(output))
        raise RuntimeError(f"Could not extract a downloadable URL from Replicate output. Debug written to {debug_path}")

    r = requests.get(out_url)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(r.content)

    return out_path

# ---------------------------------------------------------
# 3) AUTO-PLACEMENT INTO TEMPLATE
# ---------------------------------------------------------
def insert_face_into_template(stylized_path: str, out_path: str, template_path: str):
    template = Image.open(template_path).convert("RGBA")
    stylized = Image.open(stylized_path).convert("RGBA")

    template_np = cv2.cvtColor(np.array(template.convert("RGB")), cv2.COLOR_RGB2BGR)
    h_t, w_t, _ = template_np.shape

    # detect face region in template (child illustration)
    mp_face = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.4)
    result = mp_face.process(cv2.cvtColor(template_np, cv2.COLOR_BGR2RGB))

    if not result.detections:
        # fallback if model doesn't detect face
        target_x = int(w_t * 0.15)
        target_y = int(h_t * 0.20)
        target_w = int(w_t * 0.25)
        target_h = int(target_w * stylized.height / stylized.width)
    else:
        # choose largest detection
        best = None
        max_area = 0
        for det in result.detections:
            bbox = det.location_data.relative_bounding_box
            x = int(bbox.xmin * w_t)
            y = int(bbox.ymin * h_t)
            bw = int(bbox.width * w_t)
            bh = int(bbox.height * h_t)
            area = bw * bh
            if area > max_area:
                best = (x, y, bw, bh)
                max_area = area

        x, y, bw, bh = best
        pad_x = int(bw * 0.18)
        pad_y = int(bh * 0.20)

        target_x = max(0, x - pad_x)
        target_y = max(0, y - pad_y)
        target_w = min(w_t - target_x, bw + pad_x * 2)
        target_h = min(h_t - target_y, bh + pad_y * 2)

    # resize stylized face
    aspect = stylized.width / stylized.height
    new_w = target_w
    new_h = int(new_w / aspect)
    if new_h < target_h:
        new_h = target_h
        new_w = int(new_h * aspect)

    resized = stylized.resize((new_w, new_h), Image.LANCZOS)

    # center into target
    paste_x = target_x + (target_w - new_w) // 2
    paste_y = target_y + (target_h - new_h) // 2

    # soft circular mask
    mask = Image.new("L", resized.size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0,0,resized.width,resized.height), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=8))

    final = template.copy()
    final.paste(resized, (paste_x, paste_y), mask)
    final.save(out_path)

# Manual placement UI has been removed; pipeline performs automatic insertion.
