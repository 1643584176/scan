"""Read-only authorization probe for Make context-extraction derived artifacts."""

import io
import json
import sys
import urllib.error
import urllib.request


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_PUBLIC_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PRIVATE_FILE = "5Gs4PaTz11Hlk2sqVnidBG"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def post(path, body, uid=None, cookie=None, file_key=None):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/make/{file_key or ''}",
        "Content-Type": "application/json",
        "X-Figma-User-ID": uid or "",
        "X-Figma-File-Key": file_key or "",
    }
    if cookie:
        headers["Cookie"] = cookie
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")


def parse(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def status_summary(raw):
    value = parse(raw)
    if not isinstance(value, dict):
        return raw[:180]
    meta = value.get("meta")
    result = {
        "status": value.get("status"),
        "error": value.get("error"),
        "message": value.get("message"),
    }
    if isinstance(meta, dict) and isinstance(meta.get("tasks"), list):
        result["tasks"] = [
            {
                "task_id": task.get("task_id"),
                "status": task.get("status"),
                "has_result_artifact": bool(task.get("result_artifact_id")),
                "applied": task.get("applied_at") is not None,
            }
            for task in meta["tasks"]
            if isinstance(task, dict)
        ]
    return json.dumps(result, ensure_ascii=False)


cookie_a = load_cookie("ws_cookie_A_new.txt")
cookie_b = load_cookie("ws_cookie_B_new.txt")
actors = (
    ("A owner", A_UID, cookie_a),
    ("B viewer", B_UID, cookie_b),
    ("anonymous", None, None),
)
files = (
    ("A public Make", A_PUBLIC_MAKE),
    ("A private file", A_PRIVATE_FILE),
)

baselines = {}
for file_label, file_key in files:
    print(f"\n== status: {file_label} ==")
    for actor_label, uid, cookie in actors:
        code, raw = post(
            "/api/make/context_extraction/status",
            {"file_key": file_key},
            uid,
            cookie,
            file_key,
        )
        print(f"[{actor_label}] {code} {status_summary(raw)}")
        if actor_label == "A owner" and code == 200:
            baselines[file_key] = parse(raw)

for file_key, value in baselines.items():
    tasks = value.get("meta", {}).get("tasks", []) if isinstance(value, dict) else []
    task = next(
        (
            item
            for item in tasks
            if isinstance(item, dict) and item.get("result_artifact_id")
        ),
        None,
    )
    if not task:
        print(f"\n[presign {file_key}] skipped: no completed artifact")
        continue
    print(f"\n== presign existing artifact: {file_key} ==")
    for artifact_type in ("filesystem_tar", "all_fonts_json"):
        for actor_label, uid, cookie in actors:
            code, raw = post(
                "/api/make/context_extraction/artifact/presign",
                {
                    "file_key": file_key,
                    "artifact_type": artifact_type,
                    "result_artifact_id": task["result_artifact_id"],
                },
                uid,
                cookie,
                file_key,
            )
            value = parse(raw)
            has_url = bool(
                isinstance(value, dict)
                and isinstance(value.get("meta"), dict)
                and value["meta"].get("presigned_url")
            )
            message = value.get("message") if isinstance(value, dict) else raw[:120]
            print(
                f"[{artifact_type} / {actor_label}] {code} "
                f"has_presigned_url={has_url} message={message!r}"
            )
