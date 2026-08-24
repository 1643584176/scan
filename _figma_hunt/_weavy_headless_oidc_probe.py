"""Probe whether an existing Figma session can silently enter Weave OIDC.

No consent button is clicked and no credential value is printed.
"""

import argparse
import base64
import hashlib
import io
import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from playwright.sync_api import sync_playwright
import requests


ROOT = Path(__file__).resolve().parent
CLIENT_ID = "SbBGdDK0JIYzSU92FsIHQr"
REDIRECT_URI = "https://app.weavy.ai/signin"
SCOPES = "openid profile email file_content:read file_create"
FIREBASE_API_KEY = "AIzaSyC-qLy3TFyXMogJPfMkZJ9H_q46hEu1sxI"
OUTBOUND_PROXY = "http://192.168.0.199:1080"


def load_cookie_header(path: Path):
    cookies = []
    for part in io.open(path, encoding="utf-8").read().strip().split(";"):
        if "=" not in part:
            continue
        name, value = part.strip().split("=", 1)
        cookies.append(
            {
                "name": name,
                "value": value,
                "url": "https://www.figma.com",
            }
        )
    return cookies


def b64url_sha256(value: str) -> str:
    digest = hashlib.sha256(value.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label", choices=("A", "B"))
    parser.add_argument("--exchange", action="store_true")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--app-flow", action="store_true")
    parser.add_argument("--omit-nonce", action="store_true")
    args = parser.parse_args()
    cookie_path = ROOT / f"ws_cookie_{args.label}_new.txt"
    state = secrets.token_urlsafe(24)
    raw_nonce = secrets.token_urlsafe(24)
    oauth_params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "state": state,
        }
    if not args.omit_nonce:
        oauth_params["nonce"] = b64url_sha256(raw_nonce)
    query = urlencode(oauth_params)
    auth_url = f"https://www.figma.com/oauth?{query}"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="msedge",
            headless=not args.headed,
            args=(
                [
                    "--window-position=-32000,-32000",
                    "--disable-blink-features=AutomationControlled",
                ]
                if args.headed
                else None
            ),
            ignore_default_args=["--enable-automation"] if args.headed else None,
        )
        context = browser.new_context()
        context.add_cookies(load_cookie_header(cookie_path))
        page = context.new_page()
        captured = {"bearer": None, "callback_code": None, "callback_state": None}
        api_statuses = []

        def on_request(request):
            request_url = urlparse(request.url)
            if request_url.netloc == "app.weavy.ai" and request_url.path == "/signin":
                callback_params = parse_qs(request_url.query)
                if callback_params.get("code"):
                    captured["callback_code"] = callback_params["code"][0]
                    captured["callback_state"] = callback_params.get("state", [None])[0]
            authorization = request.headers.get("authorization", "")
            if request.url.startswith("https://api.weavy.ai/api/") and authorization.startswith("Bearer "):
                captured["bearer"] = authorization.removeprefix("Bearer ")

        def on_response(response):
            if response.url.startswith("https://api.weavy.ai/api/"):
                api_statuses.append((response.request.method, urlparse(response.url).path, response.status))

        page.on("request", on_request)
        page.on("response", on_response)
        if args.app_flow:
            page.goto(REDIRECT_URI, wait_until="domcontentloaded", timeout=60000)
            page.evaluate(
                "([state, nonce]) => {"
                "localStorage.setItem('weavy_figma_signin_state', state);"
                "localStorage.setItem('weavy_figma_signin_nonce', nonce);"
                "}",
                [state, raw_nonce],
            )
        response = page.goto(auth_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(20000 if args.app_flow else 3000)
        current = urlparse(page.url)
        params = parse_qs(current.query)
        callback_code = captured["callback_code"] or params.get("code", [None])[0]
        callback_state = captured["callback_state"] or params.get("state", [None])[0]
        code_received = bool(callback_code) and callback_state == state
        buttons = page.get_by_role("button").all_inner_texts()
        print(f"account={args.label}")
        print(f"initial_http={response.status if response else 'none'}")
        print(f"final_origin={current.scheme}://{current.netloc}")
        print(f"final_path={current.path}")
        print(f"title={page.title()[:120]}")
        print(f"code_received={code_received}")
        print(f"callback_query_keys={sorted(params.keys())}")
        print(f"buttons={buttons[:12]}")
        if args.app_flow:
            print(f"api_statuses={api_statuses[-20:]}")
            print(f"bearer_captured={bool(captured['bearer'])}")
            if captured["bearer"]:
                output_path = ROOT / f"weavy_auth_{args.label}.json"
                output = {"idToken": captured["bearer"]}
                io.open(output_path, "w", encoding="utf-8").write(json.dumps(output))
                print(f"saved={output_path.name}")
        if code_received and args.exchange:
            exchange_page = context.new_page()
            exchange_page.goto(
                "https://api.weavy.ai/api/v1/community/categories",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            oidc_result = exchange_page.evaluate(
                "async ([code, redirectUri]) => {"
                "const controller = new AbortController();"
                "const timer = setTimeout(() => controller.abort(), 30000);"
                "const response = await fetch('/api/v1/auth/figma/oidc/token', {"
                "method: 'POST', headers: {'Content-Type': 'application/json'},"
                "body: JSON.stringify({code, redirectUri}), signal: controller.signal});"
                "clearTimeout(timer); return {status: response.status, text: await response.text()};"
                "}",
                [callback_code, REDIRECT_URI],
            )
            print(f"weavy_exchange_http={oidc_result['status']}")
            if oidc_result["status"] < 400:
                oidc = json.loads(oidc_result["text"])
                print(f"weavy_exchange_keys={sorted(oidc.keys())}")
                oidc_path = ROOT / f"weavy_oidc_{args.label}.json"
                oidc_cache = {"rawNonce": raw_nonce, **oidc}
                io.open(oidc_path, "w", encoding="utf-8").write(json.dumps(oidc_cache))
                print(f"oidc_saved={oidc_path.name}")
                credential_params = {
                                "id_token": oidc["id_token"],
                                "providerId": "oidc.figma",
                            }
                if not args.omit_nonce:
                    credential_params["nonce"] = raw_nonce
                firebase_body = {
                        "postBody": "&" + urlencode(credential_params),
                        "requestUri": "http://localhost",
                        "returnSecureToken": True,
                    }
                firebase_response = requests.post(
                    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp"
                    f"?key={FIREBASE_API_KEY}",
                    json=firebase_body,
                    proxies={"http": OUTBOUND_PROXY, "https": OUTBOUND_PROXY},
                    timeout=45,
                )
                firebase_status = firebase_response.status_code
                firebase_text = firebase_response.text
                print(f"firebase_exchange_http={firebase_status}")
                if firebase_status < 400:
                    firebase = json.loads(firebase_text)
                    output = {
                        "idToken": firebase["idToken"],
                        "refreshToken": firebase.get("refreshToken"),
                        "expiresIn": firebase.get("expiresIn"),
                        "localId": firebase.get("localId"),
                    }
                    output_path = ROOT / f"weavy_auth_{args.label}.json"
                    io.open(output_path, "w", encoding="utf-8").write(json.dumps(output))
                    print(f"firebase_exchange_keys={sorted(firebase.keys())}")
                    print(f"saved={output_path.name}")
                else:
                    firebase_error = json.loads(firebase_text).get("error", {})
                    print(f"firebase_error={firebase_error.get('message', 'unknown')[:200]}")
            else:
                print(f"weavy_error={oidc_result['text'][:300]}")
        browser.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
