#!/usr/bin/env python3
"""Local mock CAPTCHA service for accessibility benchmark tasks.

This intentionally models CAPTCHA-like barriers for deterministic evaluation.
It does not integrate with, solve, or bypass any third-party CAPTCHA provider.
"""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
import argparse
import base64
from io import BytesIO
import html
import json
import os
import random
import string
import sys
import time


HOST = "127.0.0.1"
DEFAULT_PORT = 8765
PUZZLE_BACKGROUND_URL = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Road_in_Norway.jpg?width=640"
PUZZLE_BACKGROUND_SOURCE = "https://commons.wikimedia.org/wiki/File:Road_in_Norway.jpg"
PUZZLE_TOLERANCE = 2

CHALLENGE_TYPES = {
    "distorted_text",
    "puzzle_slider",
}

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


def png_data_uri(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def load_puzzle_background():
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Pillow is required for puzzle_slider CAPTCHA generation.") from exc

    try:
        request = Request(PUZZLE_BACKGROUND_URL, headers={"User-Agent": "WinArenaCaptchaService/1.0"})
        with urlopen(request, timeout=8) as response:
            data = response.read()
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        image = Image.new("RGB", (640, 360), "#9dc3d4")
        draw = ImageDraw.Draw(image)
        for y in range(360):
            shade = int(110 + y * 0.25)
            draw.line([(0, y), (640, y)], fill=(shade // 2, min(180, shade), min(210, shade + 30)))
        draw.rectangle([0, 230, 640, 360], fill="#5f8f4e")
        draw.polygon([(0, 250), (180, 180), (360, 260), (640, 190), (640, 360), (0, 360)], fill="#476f3a")
        draw.line([(0, 320), (300, 235), (640, 318)], fill="#d8d8d8", width=45)
        draw.line([(0, 320), (300, 235), (640, 318)], fill="#586069", width=4)
        return image


def puzzle_slider_body(seed):
    try:
        from PIL import ImageDraw, ImageFilter
    except ImportError as exc:
        raise RuntimeError("Pillow is required for puzzle_slider CAPTCHA generation.") from exc

    rng = make_rng(seed)
    canvas_width = 360
    canvas_height = 220
    piece_size = 48
    target = rng.randint(35, 75)
    x = int((canvas_width - piece_size - 18) * target / 100)
    y = rng.randint(58, 132)

    base = load_puzzle_background().resize((canvas_width, canvas_height))
    piece = base.crop((x, y, x + piece_size, y + piece_size))
    piece = piece.filter(ImageFilter.SHARPEN)

    draw = ImageDraw.Draw(base, "RGBA")
    hole_box = [x, y, x + piece_size - 1, y + piece_size - 1]
    draw.rounded_rectangle(hole_box, radius=8, fill=(255, 255, 255, 180))
    draw.rounded_rectangle(hole_box, radius=8, outline=(30, 41, 59, 230), width=3)

    body = (
        "<div class='puzzle-wrap'>"
        f"<img class='puzzle-bg' src='{png_data_uri(base)}' alt='Puzzle CAPTCHA background with one missing square'>"
        f"<img id='puzzle-piece' class='puzzle-piece' src='{png_data_uri(piece)}' alt='Puzzle piece to align' style='top: {y}px;'>"
        "</div>"
        "<input id='answer' name='answer' type='hidden' value='0'>"
        "<div id='slider-track' class='slider-track' role='slider' aria-label='Puzzle slider' "
        "aria-valuemin='0' aria-valuemax='100' aria-valuenow='0' tabindex='0'>"
        "<div id='slider-fill' class='slider-fill'></div>"
        "<div id='slider-thumb' class='slider-thumb'>></div>"
        "<div class='slider-text'>Slide to complete</div>"
        "</div>"
        "<script>"
        "const piece=document.getElementById('puzzle-piece');"
        "const answer=document.getElementById('answer');"
        "const track=document.getElementById('slider-track');"
        "const thumb=document.getElementById('slider-thumb');"
        "const fill=document.getElementById('slider-fill');"
        "const maxX=360-48-18;"
        "let dragging=false;"
        "function setSliderFromClientX(clientX){"
        "  const rect=track.getBoundingClientRect();"
        "  const maxThumb=rect.width-thumb.offsetWidth;"
        "  const px=Math.max(0,Math.min(maxThumb,clientX-rect.left-thumb.offsetWidth/2));"
        "  const value=Math.round(px*100/maxThumb);"
        "  const x=Math.round(maxX*value/100);"
        "  thumb.style.left=px+'px';"
        "  fill.style.width=(px+thumb.offsetWidth/2)+'px';"
        "  piece.style.left=x+'px';"
        "  answer.value=value;"
        "  track.setAttribute('aria-valuenow',value);"
        "}"
        "thumb.addEventListener('mousedown',e=>{dragging=true;e.preventDefault();});"
        "document.addEventListener('mousemove',e=>{if(dragging)setSliderFromClientX(e.clientX);});"
        "document.addEventListener('mouseup',()=>{dragging=false;});"
        "track.addEventListener('click',e=>setSliderFromClientX(e.clientX));"
        "track.addEventListener('keydown',e=>{"
        "  let value=Number(answer.value);"
        "  if(e.key==='ArrowRight'||e.key==='ArrowUp') value=Math.min(100,value+1);"
        "  else if(e.key==='ArrowLeft'||e.key==='ArrowDown') value=Math.max(0,value-1);"
        "  else return;"
        "  e.preventDefault();"
        "  const rect=track.getBoundingClientRect();"
        "  const maxThumb=rect.width-thumb.offsetWidth;"
        "  setSliderFromClientX(rect.left+(value*maxThumb/100)+thumb.offsetWidth/2);"
        "});"
        "setSliderFromClientX(track.getBoundingClientRect().left+thumb.offsetWidth/2);"
        "</script>"
    )
    return body, str(target)


def challenge(kind, seed):
    rng = make_rng(seed)
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
    if kind == "puzzle_slider":
        body, answer = puzzle_slider_body(seed)
        return {
            "answer": answer,
            "title": "Complete the puzzle slider",
            "panel_width": 362,
            "prompt": "",
            "body": body,
            "hint": "",
            "tolerance": PUZZLE_TOLERANCE,
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
    .puzzle-wrap {{ position: relative; width: 360px; height: 220px; margin: 16px 0; border: 1px solid #9aa5b1; background: #eef3f7; overflow: hidden; }}
    .puzzle-bg {{ display: block; width: 360px; height: 220px; }}
    .puzzle-piece {{ position: absolute; left: 0; width: 48px; height: 48px; box-sizing: border-box; border: 2px solid #1f2933; box-shadow: 0 2px 8px rgba(0,0,0,.35); }}
    .slider-track {{ position: relative; width: 360px; height: 44px; margin: 14px 0 4px; border: 1px solid #9aa5b1; background: #eef3f7; user-select: none; cursor: pointer; }}
    .slider-fill {{ position: absolute; left: 0; top: 0; height: 44px; width: 0; background: #cfe8d8; }}
    .slider-thumb {{ position: absolute; left: 0; top: 0; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: #2f6f9f; color: white; font-size: 24px; font-weight: bold; cursor: grab; z-index: 2; }}
    .slider-thumb:active {{ cursor: grabbing; }}
    .slider-text {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #52616b; pointer-events: none; }}
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
        if kind == "puzzle_slider":
            try:
                matched = abs(int(answer or "0") - int(expected)) <= item.get("tolerance", 0)
            except ValueError:
                matched = False
        else:
            matched = answer.lower() == expected.lower()
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
        if kind != "puzzle_slider":
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
