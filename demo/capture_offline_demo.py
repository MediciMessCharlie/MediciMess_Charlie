#!/usr/bin/env python3
"""Capture an offline screenshot set and MP4 tour of the MediciMess dashboard.

The script starts the API and dashboard, drives a local Google Chrome instance
through the Chrome DevTools Protocol, and writes self-contained demo assets.
No internet connection is used while capturing.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont
import websocket


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "demo" / "offline_demo"
CHROME_CANDIDATES = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
)


def wait_for_url(url: str, timeout: float = 45) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {url}")


class CDP:
    """Small synchronous Chrome DevTools Protocol client."""

    def __init__(self, websocket_url: str):
        self.socket = websocket.create_connection(websocket_url, timeout=30)
        self.counter = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self.counter += 1
        request_id = self.counter
        self.socket.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.socket.recv())
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(f"CDP {method}: {message['error']}")
            return message.get("result", {})

    def evaluate(self, expression: str):
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
        )
        return result.get("result", {}).get("value")

    def navigate(self, url: str) -> None:
        self.call("Page.navigate", {"url": url})
        self.wait_js("document.readyState === 'complete'")

    def wait_js(self, expression: str, timeout: float = 45) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if self.evaluate(expression):
                    return
            except Exception:
                pass
            time.sleep(0.25)
        raise RuntimeError(f"Timed out waiting for browser condition: {expression}")

    def screenshot(self, destination: Path, *, full_page: bool = False) -> None:
        params: dict = {"format": "png", "fromSurface": True}
        if full_page:
            metrics = self.call("Page.getLayoutMetrics")
            size = metrics["cssContentSize"]
            params["captureBeyondViewport"] = True
            params["clip"] = {
                "x": 0,
                "y": 0,
                "width": min(size["width"], 1440),
                "height": size["height"],
                "scale": 1,
            }
        encoded = self.call("Page.captureScreenshot", params)["data"]
        destination.write_bytes(base64.b64decode(encoded))

    def close(self) -> None:
        self.socket.close()


def find_chrome() -> Path:
    configured = os.environ.get("MEDICIMESS_CHROME")
    if configured and Path(configured).exists():
        return Path(configured)
    for candidate in CHROME_CANDIDATES:
        if candidate.exists():
            return candidate
    executable = shutil.which("google-chrome") or shutil.which("chromium")
    if executable:
        return Path(executable)
    raise RuntimeError("Google Chrome or Chromium was not found. Set MEDICIMESS_CHROME.")


def launch_processes(chrome: Path, profile: Path, port: int) -> tuple[list[subprocess.Popen], CDP]:
    env = os.environ.copy()
    env["MEDICIMESS_API_URL"] = "http://127.0.0.1:8000"
    env["MEDICIMESS_ARTIFACT_DIRECTORY"] = str(ROOT / "serving_outputs")
    env["MEDICIMESS_TRANSACTION_SOURCE"] = str(ROOT / "medici_transactions.csv")
    processes = [
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        ),
        subprocess.Popen(
            [sys.executable, "-c", "from dashboard.app import app; app.run(debug=False, host='127.0.0.1', port=8050)"],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        ),
    ]
    wait_for_url("http://127.0.0.1:8000/health")
    wait_for_url("http://127.0.0.1:8050/login")
    processes.append(
        subprocess.Popen(
            [
                str(chrome), "--headless=new", f"--remote-debugging-port={port}",
                "--remote-allow-origins=*", "--hide-scrollbars", "--force-device-scale-factor=1",
                "--window-size=1440,1000", f"--user-data-dir={profile}", "about:blank",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    )
    wait_for_url(f"http://127.0.0.1:{port}/json/version")
    request = Request(f"http://127.0.0.1:{port}/json", headers={"Cache-Control": "no-cache"})
    with urlopen(request) as response:
        pages = json.load(response)
    page = next(item for item in pages if item["type"] == "page")
    client = CDP(page["webSocketDebuggerUrl"])
    client.call("Page.enable")
    client.call("Runtime.enable")
    return processes, client


def capture_dashboard(client: CDP, screenshots: Path) -> None:
    client.navigate("http://127.0.0.1:8050/login")
    client.screenshot(screenshots / "01-login.png")
    client.evaluate("""
        document.querySelector('[name=username]').value = 'director';
        document.querySelector('[name=password]').value = 'medici-demo';
        document.querySelector('form').submit();
    """)
    client.wait_js("location.pathname === '/' && document.querySelectorAll('.network-table tbody tr').length > 1")
    time.sleep(2)
    client.screenshot(screenshots / "02-network-overview-dark.png", full_page=True)

    client.navigate("http://127.0.0.1:8050/branch/Florence")
    client.wait_js("document.querySelectorAll('#kpi-card-grid .kpi-card').length >= 4")
    client.evaluate("""
        document.querySelectorAll('details').forEach(x => x.open = true);
        const style = document.createElement('style');
        style.textContent = '.modebar-container, .modebar { display: none !important; }';
        document.head.appendChild(style);
        true;
    """)
    client.wait_js("document.querySelectorAll('#transaction-table tbody tr').length > 0")
    time.sleep(3)
    client.evaluate("scrollTo(0, 0); true")
    client.screenshot(screenshots / "03-florence-overview-dark.png")
    client.screenshot(screenshots / "04-florence-complete-dark.png", full_page=True)

    panels = (
        ("dashboard-panels", "05-cash-flow.png"),
        ("expense-panel", "06-expenses.png"),
        ("loan-panel", "07-loans.png"),
        ("bill-panel", "08-bills-of-exchange.png"),
        ("alert-panel", "09-anomaly-alerts.png"),
        ("transaction-panel", "10-transaction-review.png"),
    )
    for element_id, filename in panels:
        client.evaluate(f"document.getElementById('{element_id}').scrollIntoView({{block:'start'}}); true")
        time.sleep(0.8)
        client.screenshot(screenshots / filename)

    client.evaluate("document.getElementById('theme-toggle').click(); true")
    client.wait_js("document.documentElement.dataset.theme === 'light'")
    time.sleep(1)
    client.evaluate("scrollTo(0, 0); true")
    client.screenshot(screenshots / "11-florence-overview-light.png")


def title_frame(size: tuple[int, int], title: str, subtitle: str) -> Image.Image:
    image = Image.new("RGB", size, "#07110f")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 56)
    body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", 25)
    draw.ellipse((size[0] // 2 - 52, 120, size[0] // 2 + 52, 224), outline="#c89b4b", width=4)
    title_box = draw.textbbox((0, 0), title, font=title_font)
    body_box = draw.textbbox((0, 0), subtitle, font=body_font)
    draw.text(((size[0] - (title_box[2] - title_box[0])) / 2, 285), title, fill="#f3ead8", font=title_font)
    draw.text(((size[0] - (body_box[2] - body_box[0])) / 2, 375), subtitle, fill="#c89b4b", font=body_font)
    return image


def cover(image: Image.Image, size: tuple[int, int], y: int = 0) -> Image.Image:
    image = image.convert("RGB")
    if image.width != size[0]:
        ratio = size[0] / image.width
        image = image.resize((size[0], round(image.height * ratio)), Image.Resampling.LANCZOS)
    y = max(0, min(y, max(0, image.height - size[1])))
    crop = image.crop((0, y, size[0], min(y + size[1], image.height)))
    canvas = Image.new("RGB", size, "#07110f")
    canvas.paste(crop, (0, 0))
    return canvas


def caption(frame: Image.Image, heading: str, detail: str) -> Image.Image:
    frame = frame.copy()
    draw = ImageDraw.Draw(frame, "RGBA")
    draw.rectangle((0, frame.height - 122, frame.width, frame.height), fill=(7, 17, 15, 232))
    heading_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 30)
    detail_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", 19)
    draw.text((42, frame.height - 103), heading, font=heading_font, fill="#f3ead8")
    draw.text((42, frame.height - 58), detail, font=detail_font, fill="#c89b4b")
    return frame


def render_video(screenshots: Path, destination: Path) -> None:
    try:
        import imageio_ffmpeg
    except ImportError as error:
        raise RuntimeError("Install imageio-ffmpeg to render MP4: pip install imageio-ffmpeg") from error

    size, fps = (1440, 900), 12
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1440x900",
        "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium",
        "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination),
    ]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(frame: Image.Image, seconds: float) -> None:
        assert encoder.stdin is not None
        payload = frame.convert("RGB").tobytes()
        for _ in range(round(seconds * fps)):
            encoder.stdin.write(payload)

    write(title_frame(size, "Medici Bank", "Offline dashboard walkthrough"), 2.5)
    scenes = (
        ("02-network-overview-dark.png", "Network overview", "Compare every branch, aggregate totals, alerts, and outlier ratios."),
        ("03-florence-overview-dark.png", "Branch performance", "Choose a branch and reporting range; review headline KPIs and prior-year deltas."),
        ("05-cash-flow.png", "Liquidity", "Track closing cash, monthly movement, and the supporting data table."),
        ("06-expenses.png", "Operating costs", "Explore expense categories and the largest counterparties."),
        ("07-loans.png", "Credit activity", "Review issuance, repayment, counterparty share, and monthly loan activity."),
        ("08-bills-of-exchange.png", "Correspondent banking", "Inspect paginated bills-of-exchange activity from the validated ledger."),
        ("09-anomaly-alerts.png", "Risk review", "Filter anomaly alerts by severity and retain the evidence needed for triage."),
        ("10-transaction-review.png", "Validated ledger", "Search, filter, sort, and paginate the underlying transaction records."),
        ("11-florence-overview-light.png", "Two visual themes", "Switch between Florentine Day and Sicilian Night for the demo setting."),
    )
    for filename, heading, detail in scenes:
        frame = cover(Image.open(screenshots / filename), size)
        write(caption(frame, heading, detail), 2.75)
    write(title_frame(size, "Demo complete", "All views remain available in the screenshot set"), 2.5)
    assert encoder.stdin is not None
    encoder.stdin.close()
    stderr = encoder.stderr.read().decode("utf-8", errors="replace") if encoder.stderr else ""
    if encoder.wait() != 0:
        raise RuntimeError(f"FFmpeg failed:\n{stderr[-2000:]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-video", action="store_true", help="Capture PNGs only")
    args = parser.parse_args()
    screenshots = args.output / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    processes: list[subprocess.Popen] = []
    client: CDP | None = None
    with tempfile.TemporaryDirectory(prefix="medicimess-chrome-") as profile:
        try:
            processes, client = launch_processes(find_chrome(), Path(profile), 9222)
            capture_dashboard(client, screenshots)
            if not args.skip_video:
                render_video(screenshots, args.output / "medicimess-dashboard-walkthrough.mp4")
        finally:
            if client:
                client.close()
            for process in reversed(processes):
                process.terminate()
            for process in reversed(processes):
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    print(f"Offline demo written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
