"""Capture public Community generative-tool discovery traffic without logging cookies."""

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
SESSION_FILE = ROOT / "figma_session.json"
TARGET = "https://www.figma.com/community/search?resource_type=generative-plugin&query=tool"
ANONYMOUS = "--anonymous" in sys.argv

requests = []
subscriptions = []


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--disable-http2"])
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        )
    )
    if not ANONYMOUS:
        context.add_cookies(json.loads(SESSION_FILE.read_text(encoding="utf-8")))
    page = context.new_page()

    def on_request(request):
        if request.resource_type not in ("xhr", "fetch"):
            return
        entry = {"method": request.method, "url": request.url}
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = request.post_data or ""
            except UnicodeDecodeError:
                body = ""
            if len(body) <= 3000 and not re.search(r"cookie|token|authorization", body, re.I):
                entry["body"] = body
        requests.append(entry)

    def on_websocket(websocket):
        def on_sent(frame):
            if not isinstance(frame, str) or '"messageType":"subscribe"' not in frame:
                return
            try:
                message = json.loads(frame)
            except json.JSONDecodeError:
                return
            subscriptions.append(
                {
                    "viewName": message.get("viewName"),
                    "viewHash": message.get("viewHash"),
                    "args": message.get("args"),
                }
            )

        websocket.on("framesent", on_sent)

    page.on("request", on_request)
    page.on("websocket", on_websocket)
    last_error = None
    for attempt in range(3):
        try:
            page.goto(TARGET, wait_until="domcontentloaded", timeout=60000)
            last_error = None
            break
        except Exception as error:
            last_error = error
            time.sleep(3 * (attempt + 1))
    if last_error is not None:
        raise last_error
    time.sleep(20)

    links = sorted(
        {
            href.split("?")[0]
            for href in page.locator("a[href]").evaluate_all(
                "els => els.map(el => el.href)"
            )
            if "/community/generative-plugin/" in href
        }
    )

    print(f"requests={len(requests)} subscriptions={len(subscriptions)} links={len(links)}")
    print("\nSubscriptions:")
    for item in subscriptions:
        print(json.dumps(item, ensure_ascii=False))
    print("\nRelevant requests:")
    for item in requests:
        rendered = json.dumps(item, ensure_ascii=False)
        if re.search(r"/api/(search|community)", rendered, re.I):
            print(rendered[:2000])
    print("\nPublic tool links:")
    for link in links:
        print(link)

    browser.close()
