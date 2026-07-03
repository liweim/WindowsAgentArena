#!/usr/bin/env python3
"""Local mock CAPTCHA service for accessibility benchmark tasks.

This intentionally models CAPTCHA-like barriers for deterministic evaluation.
It does not integrate with, solve, or bypass any third-party CAPTCHA provider.
"""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
import argparse
import base64
from io import BytesIO
import html
import json
import mimetypes
import os
import random
import string
import sys
import time


HOST = "127.0.0.1"
DEFAULT_PORT = 8765
CAPTCHA_DATA_DIR = os.path.join(os.path.dirname(__file__), "captcha_data")
OPENCAPTCHA_TYPES = {
    "geometry_click",
    "slide_puzzle",
    "image_recognition",
    "patch_select",
    "hold_button",
}

CHALLENGE_TYPES = {
    "audio",
    "click_sequence",
    "count_chars",
    "distorted_text",
    "math",
    "robot_checkbox",
} | OPENCAPTCHA_TYPES

STARTED_AT_MTIME = os.path.getmtime(__file__)


def restart_if_code_changed():
    try:
        current_mtime = os.path.getmtime(__file__)
    except OSError:
        return
    if current_mtime <= STARTED_AT_MTIME:
        return
    print("captcha_service.py changed; restarting service.", flush=True)
    os.execv(sys.executable, [sys.executable, __file__, *sys.argv[1:]])

WORDS = [
    "river",
    "garden",
    "window",
    "market",
    "silver",
    "forest",
    "ticket",
    "planet",
]


def make_rng(seed):
    return random.Random(str(seed or "default"))


def captcha_image_data_uri(text):
    try:
        from captcha.image import ImageCaptcha
    except ImportError as exc:
        raise RuntimeError(
            "The Python package `captcha` is required. Install dependencies from "
            "src/win-arena-container/client/requirements.txt."
        ) from exc

    image = ImageCaptcha(width=330, height=100)
    buffer = BytesIO()
    image.write(text, buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def audio_captcha_data_uri(text, seed=None):
    try:
        from captcha import audio as captcha_audio
    except ImportError as exc:
        raise RuntimeError(
            "The Python package `captcha` is required. Install dependencies from "
            "src/win-arena-container/client/requirements.txt."
        ) from exc

    rng = make_rng(f"audio-{seed}-{text}")

    class ModerateAudioCaptcha(captcha_audio.AudioCaptcha):
        def _moderate_pick(self, key):
            voice = bytearray(self._cache[key][0])
            speed = rng.uniform(0.92, 1.08)
            level = rng.uniform(0.92, 1.08)
            voice = captcha_audio.change_speed(voice, speed)
            return captcha_audio.change_sound(voice, level)

        def _soft_noise(self, length):
            noise = captcha_audio.create_noise(length, 1)
            return captcha_audio.change_sound(noise, 0.18)

        def create_wave_body(self, chars):
            pause = captcha_audio.create_silence(int(captcha_audio.WAVE_SAMPLE_RATE * 0.55))
            body = bytearray()
            body.extend(captcha_audio.BEEP)
            body.extend(captcha_audio.SILENCE)
            for char in chars:
                body.extend(pause)
                body.extend(self._moderate_pick(char))
            body.extend(pause)
            body.extend(captcha_audio.END_BEEP)
            return captcha_audio.mix_wave(self._soft_noise(len(body)), body)

    audio = ModerateAudioCaptcha()
    data = audio.generate(text)
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:audio/wav;base64,{encoded}"


def png_data_uri(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def load_opencaptcha_ground_truth(kind):
    path = os.path.join(CAPTCHA_DATA_DIR, kind, "ground_truth.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def opencaptcha_image_src(kind, *parts):
    quoted = "/".join(quote(part) for part in (kind, *parts))
    return f"/captcha_data/{quoted}"


def select_opencaptcha_item(kind, seed):
    ground_truth = load_opencaptcha_ground_truth(kind)
    keys = sorted(ground_truth)
    if not keys:
        raise ValueError(f"No CAPTCHA data for {kind}")
    key = keys[make_rng(f"{kind}-{seed}").randrange(len(keys))]
    return key, ground_truth[key]


def opencaptcha_challenge(kind, seed):
    puzzle_id, data = select_opencaptcha_item(kind, seed)
    prompt = data.get("prompt") or data.get("question") or "Solve the CAPTCHA puzzle"

    if kind == "geometry_click":
        image_src = opencaptcha_image_src(kind, puzzle_id)
        body = (
            "<div class='ocw-click-board'>"
            f"<img id='ocw-click-image' src='{image_src}' alt='{html.escape(prompt, quote=True)}'>"
            "<div id='ocw-click-marker' class='ocw-click-marker'></div>"
            "</div>"
            "<input id='answer' name='answer' type='hidden' value=''>"
            "<script>"
            "const img=document.getElementById('ocw-click-image');"
            "const answer=document.getElementById('answer');"
            "const marker=document.getElementById('ocw-click-marker');"
            "img.addEventListener('click',e=>{"
            " const r=img.getBoundingClientRect();"
            " const x=Math.round((e.clientX-r.left)*img.naturalWidth/r.width);"
            " const y=Math.round((e.clientY-r.top)*img.naturalHeight/r.height);"
            " answer.value=JSON.stringify([x,y]);"
            " marker.style.left=(e.clientX-r.left)+'px'; marker.style.top=(e.clientY-r.top)+'px';"
            " marker.style.display='block';"
            "});"
            "</script>"
        )
        return {
            "answer": data.get("answer"),
            "title": "Click the requested object",
            "panel_width": 520,
            "prompt": prompt,
            "body": body,
            "hint": "",
            "ocw_type": kind,
            "puzzle_id": puzzle_id,
        }

    if kind == "slide_puzzle":
        image_src = opencaptcha_image_src(kind, puzzle_id)
        component = data.get("component_image")
        component_src = opencaptcha_image_src(kind, component)
        body = (
            "<div id='ocw-slide-board' class='ocw-slide-board'>"
            f"<img class='ocw-slide-bg' src='{image_src}' alt='{html.escape(prompt, quote=True)}'>"
            f"<img id='ocw-slide-piece' class='ocw-slide-piece' src='{component_src}' alt='Puzzle component'>"
            "</div>"
            "<input id='answer' name='answer' type='hidden' value='[0,0]'>"
            "<script>"
            "const board=document.getElementById('ocw-slide-board');"
            "const bg=board.querySelector('.ocw-slide-bg');"
            "const piece=document.getElementById('ocw-slide-piece');"
            "const answer=document.getElementById('answer');"
            "let dragging=false,dx=0,dy=0;"
            "function sizePiece(){"
            " if(!piece.naturalWidth||!piece.naturalHeight)return;"
            " const w=board.clientWidth*0.12;"
            " piece.style.width=w+'px';"
            " piece.style.height=(w*piece.naturalHeight/piece.naturalWidth)+'px';"
            "}"
            "function setPos(clientX,clientY){"
            " const r=board.getBoundingClientRect();"
            " let x=Math.max(0,Math.min(r.width-piece.offsetWidth,clientX-r.left-dx));"
            " let y=Math.max(0,Math.min(r.height-piece.offsetHeight,clientY-r.top-dy));"
            " piece.style.left=x+'px'; piece.style.top=y+'px';"
            " const scale=500/r.width;"
            " const centerX=x+piece.offsetWidth/2;"
            " const centerY=y+piece.offsetHeight/2;"
            " answer.value=JSON.stringify([Math.round(centerX*scale),Math.round(centerY*scale)]);"
            "}"
            "if(bg.complete&&piece.complete)sizePiece();"
            "bg.addEventListener('load',sizePiece);"
            "piece.addEventListener('load',sizePiece);"
            "window.addEventListener('resize',sizePiece);"
            "piece.addEventListener('pointerdown',e=>{dragging=true;piece.setPointerCapture(e.pointerId);const pr=piece.getBoundingClientRect();dx=e.clientX-pr.left;dy=e.clientY-pr.top;e.preventDefault();});"
            "piece.addEventListener('pointermove',e=>{if(dragging)setPos(e.clientX,e.clientY);});"
            "piece.addEventListener('pointerup',()=>{dragging=false;});"
            "</script>"
        )
        return {
            "answer": data.get("target_position"),
            "title": "Drag the slider component",
            "panel_width": 520,
            "prompt": prompt,
            "body": body,
            "hint": "",
            "tolerance": data.get("tolerance", 10),
            "ocw_type": kind,
            "puzzle_id": puzzle_id,
        }

    if kind == "image_recognition":
        subfolder = data.get("subfolder", puzzle_id)
        images = data.get("images", [])
        buttons = []
        for idx, filename in enumerate(images):
            src = opencaptcha_image_src(kind, subfolder, filename)
            buttons.append(
                "<button type='button' class='ocw-grid-cell' data-index='{idx}'>"
                "<img src='{src}' alt='Option {num}'>"
                "</button>".format(idx=idx, src=src, num=idx + 1)
            )
        body = (
            "<div class='ocw-image-grid'>" + "".join(buttons) + "</div>"
            "<input id='answer' name='answer' type='hidden' value='[]'>"
            "<script>"
            "const answer=document.getElementById('answer'); const selected=new Set();"
            "document.querySelectorAll('.ocw-grid-cell').forEach(btn=>btn.addEventListener('click',()=>{"
            " const i=Number(btn.dataset.index); if(selected.has(i)){selected.delete(i);btn.classList.remove('selected');}else{selected.add(i);btn.classList.add('selected');}"
            " answer.value=JSON.stringify([...selected].sort((a,b)=>a-b));"
            "}));"
            "</script>"
        )
        return {
            "answer": data.get("correct_selections", []),
            "title": "Select matching images",
            "panel_width": 520,
            "prompt": data.get("question", prompt),
            "body": body,
            "hint": "",
            "ocw_type": kind,
            "puzzle_id": puzzle_id,
        }

    if kind == "patch_select":
        image_src = opencaptcha_image_src(kind, puzzle_id)
        rows, cols = data.get("grid_size", [5, 5])
        cells = "".join(
            f"<button type='button' class='ocw-patch-cell' data-index='{idx}' aria-label='Patch {idx + 1}'></button>"
            for idx in range(rows * cols)
        )
        body = (
            f"<div class='ocw-patch-board' style='--rows:{rows};--cols:{cols};'>"
            f"<img src='{image_src}' alt='{html.escape(prompt, quote=True)}'>"
            "<div class='ocw-patch-grid'>" + cells + "</div>"
            "</div>"
            "<input id='answer' name='answer' type='hidden' value='[]'>"
            "<script>"
            "const answer=document.getElementById('answer'); const selected=new Set();"
            "document.querySelectorAll('.ocw-patch-cell').forEach(btn=>btn.addEventListener('click',()=>{"
            " const i=Number(btn.dataset.index); if(selected.has(i)){selected.delete(i);btn.classList.remove('selected');}else{selected.add(i);btn.classList.add('selected');}"
            " answer.value=JSON.stringify([...selected].sort((a,b)=>a-b));"
            "}));"
            "</script>"
        )
        return {
            "answer": data.get("correct_patches", []),
            "title": "Select all matching squares",
            "panel_width": 520,
            "prompt": prompt,
            "body": body,
            "hint": "",
            "ocw_type": kind,
            "puzzle_id": puzzle_id,
        }

    if kind == "hold_button":
        image_src = opencaptcha_image_src(kind, puzzle_id)
        hold_time = float(data.get("hold_time", 3))
        body = (
            f"<figure class='ocw-hold-figure'><img src='{image_src}' alt='{html.escape(prompt, quote=True)}'></figure>"
            "<input id='answer' name='answer' type='hidden' value='0'>"
            f"<button type='button' id='ocw-hold-button' class='ocw-hold-button' data-hold='{hold_time}'>Hold</button>"
            "<div class='ocw-hold-meter'><div id='ocw-hold-fill'></div></div>"
            "<script>"
            "const btn=document.getElementById('ocw-hold-button');"
            "const fill=document.getElementById('ocw-hold-fill');"
            "const answer=document.getElementById('answer');"
            "const required=Number(btn.dataset.hold); let start=0,timer=null;"
            "function stop(){if(!start)return; const held=(performance.now()-start)/1000; answer.value=held.toFixed(2); clearInterval(timer); start=0;}"
            "btn.addEventListener('pointerdown',e=>{start=performance.now();btn.setPointerCapture(e.pointerId);timer=setInterval(()=>{const held=(performance.now()-start)/1000;fill.style.width=Math.min(100,held*100/required)+'%';answer.value=held.toFixed(2);if(held>=required){btn.textContent='Complete';}},50);});"
            "btn.addEventListener('pointerup',stop); btn.addEventListener('pointercancel',stop); btn.addEventListener('pointerleave',stop);"
            "</script>"
        )
        return {
            "answer": hold_time,
            "title": "Hold the button",
            "panel_width": 540,
            "prompt": prompt,
            "body": body,
            "hint": "",
            "ocw_type": kind,
            "puzzle_id": puzzle_id,
        }

    raise ValueError(f"Unsupported OpenCaptchaWorld type: {kind}")


def robot_checkbox_challenge():
    image_src = opencaptcha_image_src("robot_checkbox", "not_robot.png")
    body = (
        "<div class='robot-checkbox-wrap'>"
        f"<img src='{image_src}' alt=\"I'm not a robot CAPTCHA checkbox\">"
        "<button type='button' id='robot-checkbox-button' class='robot-checkbox-button' "
        "aria-label=\"I'm not a robot\"></button>"
        "<span id='robot-checkmark' class='robot-checkmark'>✓</span>"
        "</div>"
        "<input id='answer' name='answer' type='hidden' value=''>"
        "<script>"
        "const startedAt=performance.now();"
        "const answer=document.getElementById('answer');"
        "const button=document.getElementById('robot-checkbox-button');"
        "const checkmark=document.getElementById('robot-checkmark');"
        "button.addEventListener('click',()=>{"
        " const elapsed=(performance.now()-startedAt)/1000;"
        " answer.value=JSON.stringify({checked:true,elapsed});"
        " checkmark.style.display='block';"
        "});"
        "</script>"
    )
    return {
        "answer": {"checked": True, "min_elapsed": 0.7},
        "title": "Confirm you are not a robot",
        "panel_width": 645,
        "prompt": "",
        "body": body,
        "hint": "",
    }


def click_sequence_body(seed):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required for click_sequence CAPTCHA generation.") from exc

    rng = make_rng(seed)
    canvas_width = 420
    canvas_height = 260
    alphabet = string.ascii_uppercase + string.digits
    target = "".join(rng.choice(alphabet) for _ in range(5))
    distractors = [rng.choice(alphabet) for _ in range(13)]
    chars = list(target) + distractors
    rng.shuffle(chars)

    image = Image.new("RGB", (canvas_width, canvas_height), "#eef3f7")
    draw = ImageDraw.Draw(image)
    for _ in range(28):
        x1 = rng.randint(0, canvas_width)
        y1 = rng.randint(0, canvas_height)
        x2 = rng.randint(0, canvas_width)
        y2 = rng.randint(0, canvas_height)
        color = (
            rng.randint(165, 215),
            rng.randint(175, 225),
            rng.randint(185, 235),
        )
        draw.line([(x1, y1), (x2, y2)], fill=color, width=rng.randint(1, 3))

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
    except OSError:
        font = ImageFont.load_default()

    positions = []
    min_distance = 58
    for char in chars:
        for _ in range(200):
            x = rng.randint(28, canvas_width - 28)
            y = rng.randint(30, canvas_height - 30)
            if all((x - px) ** 2 + (y - py) ** 2 >= min_distance ** 2 for px, py in positions):
                positions.append((x, y))
                break
        else:
            positions.append((rng.randint(28, canvas_width - 28), rng.randint(30, canvas_height - 30)))

    items = []
    for idx, (char, (x, y)) in enumerate(zip(chars, positions)):
        color = (
            rng.randint(35, 110),
            rng.randint(45, 120),
            rng.randint(55, 135),
        )
        angle = rng.randint(-22, 22)
        text_layer = Image.new("RGBA", (58, 58), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        text_draw.text((29, 29), char, fill=color + (255,), font=font, anchor="mm")
        rotated = text_layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        image.paste(rotated, (x - 29, y - 29), rotated)
        items.append({"id": f"char-{idx}", "char": char, "x": x, "y": y})

    buttons = []
    for item in items:
        label = html.escape(item["char"])
        buttons.append(
            "<button type='button' class='click-hotspot' "
            f"style='left: {item['x'] - 21}px; top: {item['y'] - 21}px;' "
            f"data-char='{label}' aria-label='Click {label}'></button>"
        )

    body = (
        f"<p class='click-target'>Click these characters in order: <strong>{html.escape(target)}</strong></p>"
        "<div id='click-board' class='click-board'>"
        f"<img class='click-image' src='{png_data_uri(image)}' alt='CAPTCHA image with scattered letters and digits'>"
        + "".join(buttons)
        + "</div>"
        "<input id='answer' name='answer' type='hidden' value=''>"
        "<div class='click-status' aria-live='polite'>Selected: <span id='click-selection'></span></div>"
        "<button type='button' id='click-reset'>Reset selection</button>"
        "<script>"
        "const answer=document.getElementById('answer');"
        "const selection=document.getElementById('click-selection');"
        "document.querySelectorAll('.click-hotspot').forEach(button=>{"
        "  button.addEventListener('click',()=>{"
        "    answer.value+=button.dataset.char;"
        "    selection.textContent=answer.value;"
        "    button.classList.add('clicked');"
        "  });"
        "});"
        "document.getElementById('click-reset').addEventListener('click',()=>{"
        "  answer.value='';"
        "  selection.textContent='';"
        "  document.querySelectorAll('.click-hotspot').forEach(button=>button.classList.remove('clicked'));"
        "});"
        "</script>"
    )
    return body, target


def math_expression_image_data_uri(expression, rng):
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required for math CAPTCHA generation.") from exc

    def tokenize(value):
        tokens = []
        current = ""
        for char in value:
            if char.isalnum():
                current += char
            else:
                if current:
                    tokens.append(current)
                    current = ""
                if not char.isspace():
                    tokens.append(char)
        if current:
            tokens.append(current)
        return tokens

    def load_font(name, size):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            return ImageFont.load_default()

    font_names = [
        "Arial.TTF",
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSerif.ttf",
        "DejaVuSerif-Bold.ttf",
        "DejaVuSansMono.ttf",
    ]
    tokens = tokenize(expression)
    canvas_width = 420
    canvas_height = 126
    image = Image.new("RGB", (canvas_width, canvas_height), "#eef3f7")
    draw = ImageDraw.Draw(image)

    for _ in range(22):
        color = (
            rng.randint(170, 220),
            rng.randint(175, 225),
            rng.randint(180, 230),
        )
        draw.line(
            [
                (rng.randint(0, canvas_width), rng.randint(0, canvas_height)),
                (rng.randint(0, canvas_width), rng.randint(0, canvas_height)),
            ],
            fill=color,
            width=rng.randint(1, 2),
        )

    rendered = []
    for token in tokens:
        font = load_font(rng.choice(font_names), rng.randint(32, 44))
        bbox = draw.textbbox((0, 0), token, font=font)
        width = bbox[2] - bbox[0] + 28
        height = bbox[3] - bbox[1] + 28
        color = (
            rng.randint(25, 105),
            rng.randint(35, 115),
            rng.randint(45, 125),
        )
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.text(
            (width // 2, height // 2),
            token,
            fill=color + (255,),
            font=font,
            anchor="mm",
        )
        layer = layer.rotate(rng.uniform(-10, 10), resample=Image.Resampling.BICUBIC, expand=True)
        rendered.append((layer, rng.randint(8, 14)))

    margin_x = 18
    margin_y = 14
    available_width = canvas_width - 2 * margin_x
    available_height = canvas_height - 2 * margin_y
    total_width = sum(layer.width for layer, gap in rendered) + sum(gap for _, gap in rendered[:-1])
    max_height = max(layer.height for layer, _ in rendered)
    scale = min(1.0, available_width / total_width, available_height / max_height)
    if scale < 1.0:
        scaled = []
        for layer, gap in rendered:
            size = (max(1, int(layer.width * scale)), max(1, int(layer.height * scale)))
            scaled.append((layer.resize(size, Image.Resampling.LANCZOS), max(6, int(gap * scale))))
        rendered = scaled
        total_width = sum(layer.width for layer, gap in rendered) + sum(gap for _, gap in rendered[:-1])
        max_height = max(layer.height for layer, _ in rendered)

    if total_width > available_width or max_height > available_height:
        scale = min(available_width / total_width, available_height / max_height) * 0.98
        scaled = []
        for layer, gap in rendered:
            size = (max(1, int(layer.width * scale)), max(1, int(layer.height * scale)))
            scaled.append((layer.resize(size, Image.Resampling.LANCZOS), max(4, int(gap * scale))))
        rendered = scaled
        total_width = sum(layer.width for layer, gap in rendered) + sum(gap for _, gap in rendered[:-1])

    x = margin_x + max(0, (available_width - total_width) // 2)
    center_y = canvas_height // 2
    for index, (layer, gap) in enumerate(rendered):
        base_y = center_y - layer.height // 2
        min_jitter = margin_y - base_y
        max_jitter = canvas_height - margin_y - layer.height - base_y
        jitter = rng.randint(max(-8, min_jitter), min(8, max_jitter))
        y = base_y + jitter
        if x < margin_x or y < margin_y or x + layer.width > canvas_width - margin_x or y + layer.height > canvas_height - margin_y:
            raise RuntimeError("Math CAPTCHA token layout exceeded image bounds.")
        image.paste(layer, (x, y), layer)
        x += layer.width
        if index < len(rendered) - 1:
            x += gap

    image = image.filter(ImageFilter.SMOOTH)
    return png_data_uri(image)


def math_challenge_body(seed):
    rng = make_rng(seed)
    pattern = rng.choice(["multiply_add_minus", "group_multiply_minus", "divide_plus_minus", "group_minus_add"])

    if pattern == "multiply_add_minus":
        a = rng.randint(7, 19)
        b = rng.randint(4, 12)
        c = rng.randint(8, 35)
        d = rng.randint(4, 28)
        answer = a * b + c - d
        expression = f"{a} x {b} + {c} - {d}"
    elif pattern == "group_multiply_minus":
        a = rng.randint(3, 9)
        b = rng.randint(4, 12)
        c = rng.randint(3, 8)
        d = rng.randint(8, 45)
        answer = (a + b) * c - d
        expression = f"({a} + {b}) x {c} - {d}"
    elif pattern == "divide_plus_minus":
        divisor = rng.randint(3, 9)
        quotient = rng.randint(9, 26)
        offset = rng.randint(12, 55)
        d = rng.randint(3, 24)
        dividend = divisor * quotient
        answer = dividend // divisor + offset - d
        expression = f"{dividend} / {divisor} + {offset} - {d}"
    else:
        a = rng.randint(5, 14)
        b = rng.randint(3, 9)
        c = rng.randint(18, 72)
        d = rng.randint(5, 30)
        answer = (a * b) - c + d
        expression = f"({a} x {b}) - {c} + {d}"

    image_src = math_expression_image_data_uri(expression, rng)
    body = (
        "<figure class='math-captcha'>"
        f"<img src='{image_src}' alt='Math CAPTCHA expression image'>"
        "</figure>"
    )
    return body, str(answer)


def count_chars_image_data_uri(text, rng):
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required for count_chars CAPTCHA generation.") from exc

    def load_font(name, size):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            return ImageFont.load_default()

    font_names = [
        "Arial.TTF",
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSerif.ttf",
        "DejaVuSerif-Bold.ttf",
        "DejaVuSansMono.ttf",
    ]
    canvas_width = 420
    canvas_height = 152
    margin_x = 18
    row_ys = [34, 78, 122]
    image = Image.new("RGB", (canvas_width, canvas_height), "#eef3f7")
    draw = ImageDraw.Draw(image)

    for _ in range(30):
        color = (
            rng.randint(170, 225),
            rng.randint(175, 230),
            rng.randint(180, 235),
        )
        draw.line(
            [
                (rng.randint(0, canvas_width), rng.randint(0, canvas_height)),
                (rng.randint(0, canvas_width), rng.randint(0, canvas_height)),
            ],
            fill=color,
            width=rng.randint(1, 2),
        )

    chars_per_row = 12
    cell_width = (canvas_width - 2 * margin_x) / chars_per_row
    for idx, char in enumerate(text):
        row = idx // chars_per_row
        col = idx % chars_per_row
        x = int(margin_x + col * cell_width + cell_width / 2 + rng.randint(-3, 3))
        y = row_ys[row] + rng.randint(-5, 5)
        font = load_font(rng.choice(font_names), rng.randint(24, 32))
        color = (
            rng.randint(25, 105),
            rng.randint(35, 115),
            rng.randint(45, 125),
        )
        layer = Image.new("RGBA", (46, 46), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.text((23, 23), char, fill=color + (255,), font=font, anchor="mm")
        layer = layer.rotate(rng.uniform(-14, 14), resample=Image.Resampling.BICUBIC, expand=False)
        image.paste(layer, (x - 23, y - 23), layer)

    image = image.filter(ImageFilter.SMOOTH)
    return png_data_uri(image)


def count_chars_body(seed):
    rng = make_rng(seed)
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    target = rng.choice(alphabet)
    count = rng.randint(3, 6)
    others = [char for char in alphabet if char != target]
    chars = [target] * count + [rng.choice(others) for _ in range(36 - count)]
    rng.shuffle(chars)
    text = "".join(chars)
    image_src = count_chars_image_data_uri(text, rng)
    body = (
        f"<p class='count-target'>How many times does <strong>{html.escape(target)}</strong> appear?</p>"
        "<figure class='count-captcha'>"
        f"<img src='{image_src}' alt='CAPTCHA image with a random character string'>"
        "</figure>"
    )
    return body, str(count)


def challenge(kind, seed):
    rng = make_rng(seed)
    if kind in OPENCAPTCHA_TYPES:
        return opencaptcha_challenge(kind, seed)
    if kind == "robot_checkbox":
        return robot_checkbox_challenge()
    if kind == "audio":
        audio_choices = string.digits
        code = "".join(rng.choice(audio_choices) for _ in range(5))
        audio_src = audio_captcha_data_uri(code, seed)
        return {
            "answer": code,
            "title": "Type the audio verification code",
            "panel_width": 356,
            "prompt": "Listen to the audio and enter the five digits you hear.",
            "body": (
                "<div class='audio-captcha'>"
                f"<audio controls src='{audio_src}'>"
                "Your browser does not support the audio element."
                "</audio>"
                "</div>"
            ),
            "hint": "",
        }
    if kind == "click_sequence":
        body, answer = click_sequence_body(seed)
        return {
            "answer": answer,
            "title": "Click the characters in order",
            "panel_width": 422,
            "prompt": "",
            "body": body,
            "hint": "",
        }
    if kind == "count_chars":
        body, answer = count_chars_body(seed)
        return {
            "answer": answer,
            "title": "Count the target character",
            "panel_width": 420,
            "prompt": "",
            "body": body,
            "hint": "",
        }
    if kind == "distorted_text":
        code = "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(5))
        image_src = captcha_image_data_uri(code)
        return {
            "answer": code,
            "title": "Type the verification code",
            "panel_width": 356,
            "prompt": "",
            "body": (
                "<figure class='captcha-figure'>"
                f"<img src='{image_src}' alt='Distorted CAPTCHA image'>"
                "</figure>"
            ),
            "hint": "",
        }
    if kind == "math":
        body, answer = math_challenge_body(seed)
        return {
            "answer": answer,
            "title": "Solve the verification problem",
            "panel_width": 420,
            "prompt": "Calculate the value of the expression.",
            "body": body,
            "hint": "",
        }
    raise ValueError(f"Unsupported challenge type: {kind}")


def page_template(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #1f2933; background: #f5f7fa; }}
    main {{ width: fit-content; max-width: calc(100vw - 64px); margin: 48px auto; padding: 32px; background: white; border: 1px solid #d8dee9; }}
    .captcha-panel {{ width: var(--panel-width); max-width: 100%; }}
    h1 {{ max-width: 100%; font-size: 28px; margin: 0 0 16px; overflow-wrap: anywhere; }}
    p {{ font-size: 18px; line-height: 1.5; }}
    label, input, button, summary {{ font-size: 18px; }}
    label {{ display: block; }}
    input[type=text] {{ display: block; width: 356px; max-width: 100%; box-sizing: border-box; padding: 12px; margin: 12px 0 16px; }}
    button {{ padding: 10px 14px; margin: 6px 6px 6px 0; cursor: pointer; }}
    .captcha-figure {{ display: block; width: 356px; max-width: 100%; box-sizing: border-box; margin: 16px 0; padding: 12px; border: 1px solid #9aa5b1; background: #eef3f7; }}
    .captcha-figure img {{ display: block; width: 330px; height: 100px; }}
    .audio-captcha {{ width: 356px; max-width: 100%; box-sizing: border-box; margin: 16px 0; padding: 12px; border: 1px solid #9aa5b1; background: #eef3f7; }}
    .audio-captcha audio {{ display: block; width: 100%; }}
    .math-captcha {{ width: 420px; max-width: 100%; box-sizing: border-box; margin: 16px 0; padding: 0; border: 1px solid #9aa5b1; background: #eef3f7; }}
    .math-captcha img {{ display: block; width: 420px; height: 126px; max-width: 100%; }}
    .click-target {{ margin: 8px 0 12px; }}
    .click-board {{ position: relative; width: 420px; height: 260px; margin: 16px 0 12px; border: 1px solid #9aa5b1; background: #eef3f7; overflow: hidden; }}
    .click-image {{ display: block; width: 420px; height: 260px; }}
    .click-hotspot {{ position: absolute; width: 42px; height: 42px; padding: 0; margin: 0; border: 2px solid transparent; border-radius: 50%; background: transparent; cursor: pointer; }}
    .click-hotspot:hover, .click-hotspot:focus {{ border-color: #2f6f9f; outline: none; }}
    .click-hotspot.clicked {{ border-color: #126b3a; background: rgba(18, 107, 58, .14); }}
    .click-status {{ min-height: 24px; margin: 8px 0 6px; color: #52616b; font-size: 16px; }}
    .count-target {{ margin: 8px 0 12px; }}
    .count-captcha {{ width: 420px; max-width: 100%; box-sizing: border-box; margin: 16px 0; padding: 0; border: 1px solid #9aa5b1; background: #eef3f7; }}
    .count-captcha img {{ display: block; width: 420px; height: 152px; max-width: 100%; }}
    .ocw-click-board {{ position: relative; width: fit-content; max-width: 100%; margin: 16px 0; border: 1px solid #9aa5b1; background: #eef3f7; }}
    .ocw-click-board img {{ display: block; max-width: 100%; height: auto; cursor: crosshair; }}
    .ocw-click-marker {{ display: none; position: absolute; width: 18px; height: 18px; margin: -9px 0 0 -9px; border: 2px solid #126b3a; background: rgba(18,107,58,.25); border-radius: 50%; pointer-events: none; }}
    .ocw-slide-board {{ position: relative; width: 500px; max-width: 100%; margin: 16px 0; border: 1px solid #9aa5b1; background: #eef3f7; overflow: hidden; touch-action: none; }}
    .ocw-slide-bg {{ display: block; width: 100%; height: auto; }}
    .ocw-slide-piece {{ position: absolute; left: 0; top: 0; cursor: grab; touch-action: none; filter: drop-shadow(0 2px 5px rgba(0,0,0,.35)); }}
    .ocw-slide-piece:active {{ cursor: grabbing; }}
    .ocw-image-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; width: 420px; max-width: 100%; margin: 16px 0; }}
    .ocw-grid-cell {{ padding: 0; margin: 0; border: 3px solid #d8dee9; background: white; aspect-ratio: 1 / 1; overflow: hidden; }}
    .ocw-grid-cell img {{ display: block; width: 100%; height: 100%; object-fit: cover; }}
    .ocw-grid-cell.selected {{ border-color: #126b3a; box-shadow: inset 0 0 0 3px rgba(18,107,58,.25); }}
    .ocw-patch-board {{ position: relative; width: fit-content; max-width: 100%; margin: 16px 0; border: 1px solid #9aa5b1; background: #eef3f7; }}
    .ocw-patch-board img {{ display: block; max-width: 100%; height: auto; }}
    .ocw-patch-grid {{ position: absolute; inset: 0; display: grid; grid-template-columns: repeat(var(--cols), 1fr); grid-template-rows: repeat(var(--rows), 1fr); }}
    .ocw-patch-cell {{ padding: 0; margin: 0; border: 1px solid rgba(255,255,255,.8); background: transparent; }}
    .ocw-patch-cell.selected {{ background: rgba(18,107,58,.28); box-shadow: inset 0 0 0 3px #126b3a; }}
    .ocw-hold-figure {{ width: 540px; max-width: 100%; margin: 16px 0; padding: 0; border: 1px solid #9aa5b1; background: #eef3f7; }}
    .ocw-hold-figure img {{ display: block; width: 100%; height: auto; }}
    .ocw-hold-button {{ display: block; width: 540px; max-width: 100%; height: 56px; margin: 14px 0 8px; background: #2f6f9f; color: white; border: 0; font-weight: bold; }}
    .ocw-hold-meter {{ width: 540px; max-width: 100%; height: 12px; background: #d8dee9; }}
    .ocw-hold-meter div {{ height: 100%; width: 0; background: #126b3a; }}
    .robot-checkbox-wrap {{ position: relative; width: 645px; max-width: 100%; margin: 16px 0; }}
    .robot-checkbox-wrap img {{ display: block; width: 100%; height: auto; }}
    .robot-checkbox-button {{ position: absolute; left: 7.4%; top: 34.4%; width: 8.7%; height: 30.6%; padding: 0; margin: 0; border: 0; background: transparent; cursor: pointer; }}
    .robot-checkbox-button:focus {{ outline: none; }}
    .robot-checkmark {{ display: none; position: absolute; left: 9.3%; top: 36.6%; color: #126b3a; font-size: 38px; line-height: 1; font-weight: bold; pointer-events: none; }}
    .hint {{ margin-top: 18px; color: #52616b; }}
    .error {{ color: #a61b1b; font-weight: bold; }}
    .success {{ color: #126b3a; font-weight: bold; }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>"""


def parse_json_answer(answer):
    try:
        return json.loads(answer)
    except json.JSONDecodeError:
        return None


def point_in_area(point, answer):
    if not isinstance(point, list) or len(point) != 2:
        return False
    if not isinstance(answer, dict) or "area" not in answer:
        return False
    try:
        (min_x, min_y), (max_x, max_y) = answer["area"]
        x, y = point
        return min_x <= x <= max_x and min_y <= y <= max_y
    except (TypeError, ValueError):
        return False


def same_index_set(left, right):
    if not isinstance(left, list):
        return False
    try:
        return set(int(v) for v in left) == set(int(v) for v in right)
    except (TypeError, ValueError):
        return False


def verify_challenge_answer(kind, answer, item):
    expected = item["answer"]
    if kind == "robot_checkbox":
        value = parse_json_answer(answer)
        if not isinstance(value, dict) or not value.get("checked"):
            return False
        try:
            return float(value.get("elapsed", 0)) >= float(expected.get("min_elapsed", 0.7))
        except (TypeError, ValueError):
            return False
    if kind == "geometry_click":
        return point_in_area(parse_json_answer(answer), expected)
    if kind == "slide_puzzle":
        value = parse_json_answer(answer)
        if not isinstance(value, list) or len(value) != 2:
            return False
        try:
            x, y = float(value[0]), float(value[1])
            target_x, target_y = float(expected[0]), float(expected[1])
            tolerance = float(item.get("tolerance", 10))
            return ((x - target_x) ** 2 + (y - target_y) ** 2) ** 0.5 <= tolerance
        except (TypeError, ValueError, IndexError):
            return False
    if kind in {"image_recognition", "patch_select"}:
        return same_index_set(parse_json_answer(answer), expected)
    if kind == "hold_button":
        try:
            return float(answer) >= float(expected)
        except (TypeError, ValueError):
            return False
    return answer.lower() == str(expected).lower()


class Handler(BaseHTTPRequestHandler):
    server_version = "MockCaptcha/1.0"

    def do_GET(self):
        restart_if_code_changed()
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.render_index()
            return
        if parsed.path == "/captcha":
            self.render_captcha(parsed)
            return
        if parsed.path == "/success":
            self.render_success(parsed)
            return
        if parsed.path.startswith("/captcha_data/"):
            self.serve_captcha_data(parsed.path)
            return
        if parsed.path == "/status":
            self.write_json({"ok": True, "records": self.server.records})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        restart_if_code_changed()
        parsed = urlparse(self.path)
        if parsed.path != "/verify":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        kind = data.get("type", ["text"])[0]
        seed = data.get("seed", ["default"])[0]
        session = data.get("session", ["default"])[0]
        answer = data.get("answer", [""])[0].strip()
        item = challenge(kind, seed)
        expected = item["answer"]
        matched = verify_challenge_answer(kind, answer, item)
        if matched:
            self.server.records[session] = {
                "type": kind,
                "seed": seed,
                "solved": True,
                "answer": expected,
                "timestamp": time.time(),
            }
            params = urlencode({"type": kind, "seed": seed, "session": session})
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/success?{params}")
            self.end_headers()
            return
        params = urlencode({"type": kind, "seed": seed, "session": session, "error": "1"})
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", f"/captcha?{params}")
        self.end_headers()

    def render_index(self):
        links = []
        for kind in sorted(CHALLENGE_TYPES):
            href = "/captcha?" + urlencode({"type": kind, "seed": "demo", "session": f"demo-{kind}"})
            links.append(f"<li><a href='{href}'>{html.escape(kind.replace('_', ' '))}</a></li>")
        body = "<h1>Mock CAPTCHA service</h1><p>Choose a deterministic challenge type.</p><ul>" + "".join(links) + "</ul>"
        self.write_html(page_template("Mock CAPTCHA service", body))

    def render_captcha(self, parsed):
        query = parse_qs(parsed.query)
        kind = query.get("type", ["text"])[0]
        seed = query.get("seed", ["default"])[0]
        session = query.get("session", [f"{kind}-{seed}"])[0]
        if kind not in CHALLENGE_TYPES:
            self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported challenge type")
            return
        item = challenge(kind, seed)
        error = "<p class='error'>That answer did not match. Try again.</p>" if query.get("error") else ""
        input_html = ""
        if kind not in {"click_sequence", "robot_checkbox", *OPENCAPTCHA_TYPES}:
            input_html = "<label for='answer'>Answer</label><input id='answer' name='answer' type='text' autocomplete='off'>"
        prompt_html = f"<p>{html.escape(item['prompt'])}</p>" if item.get("prompt") else ""
        hint_html = f"<p class=\"hint\">{html.escape(item['hint'])}</p>" if item.get("hint") else ""
        panel_width = int(item.get("panel_width", 360))
        body = f"""
<div class="captcha-panel" style="--panel-width: {panel_width}px;">
<h1>{html.escape(item['title'])}</h1>
{prompt_html}
{error}
<form method="post" action="/verify">
  <input type="hidden" name="type" value="{html.escape(kind)}">
  <input type="hidden" name="seed" value="{html.escape(seed)}">
  <input type="hidden" name="session" value="{html.escape(session)}">
  {item['body']}
  {input_html}
  <button type="submit">Continue</button>
</form>
{hint_html}
</div>
"""
        self.write_html(page_template(item["title"], body))

    def render_success(self, parsed):
        query = parse_qs(parsed.query)
        session = query.get("session", ["default"])[0]
        body = f"""
<h1 class="success">Verification complete</h1>
"""
        self.write_html(page_template("Verification complete", body))

    def serve_captcha_data(self, path):
        relative = unquote(path.removeprefix("/captcha_data/"))
        full_path = os.path.realpath(os.path.join(CAPTCHA_DATA_DIR, relative))
        data_root = os.path.realpath(CAPTCHA_DATA_DIR)
        if not full_path.startswith(data_root + os.sep) or not os.path.isfile(full_path):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        mime, _ = mimetypes.guess_type(full_path)
        if not mime:
            mime = "application/octet-stream"
        with open(full_path, "rb") as f:
            data = f.read()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def write_html(self, data):
        encoded = data.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def write_json(self, data):
        encoded = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="Run a local mock CAPTCHA service.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.records = {}
    print(f"Mock CAPTCHA service listening on http://{args.host}:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
