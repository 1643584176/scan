"""Test privacy_mode=user isolation inside an owner-controlled public Make file."""

import asyncio
import io
import json
import sys
import urllib.error
import urllib.request
import uuid

import websockets


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
FILE_KEY = "5zb5YkoxMa09KpqOyuLcHD"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
THREADS_HASH = "3ebe8bcd1ab2477b47769f9f4463b6541a104b6d6762402c7ffadd514bfbe08c"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip().replace("\n", "; ")


def rest(method, path, body, uid, cookie):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/make/{FILE_KEY}",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "X-Figma-User-ID": uid,
        "X-Figma-File-Key": FILE_KEY,
    }
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode(errors="replace"))
    except urllib.error.HTTPError as error:
        raw = error.read().decode(errors="replace")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = {"message": raw[:180]}
        return error.code, value


def livegraph_url(uid):
    return (
        "wss://www.figma.com/api/livegraph?pv=1&userId="
        + (uid or "")
        + "&anonUserId=&clientType=web&preload=%7B%7D&requestedProtocolVersion=2"
        + "&clientUrl=https%3A%2F%2Fwww.figma.com%2Fmake%2F"
        + FILE_KEY
        + "&connectionType=initial&reconnect=0"
    )


def auth_message(uid):
    return {
        "messageType": "auth",
        "clientType": "web",
        "args": {"userId": uid, "anonymousUserId": None},
        "tags": {"clientType": "web", "clientUrl": f"{BASE}/make/{FILE_KEY}"},
        "clientRequestedVersion": 2,
    }


async def visible_threads(label, uid=None, cookie=None):
    headers = {"User-Agent": UA, "Origin": BASE}
    if cookie:
        headers["Cookie"] = cookie
    frames = []
    async with websockets.connect(
        livegraph_url(uid),
        additional_headers=headers,
        max_size=50_000_000,
        open_timeout=15,
    ) as websocket:
        await websocket.send(json.dumps(auth_message(uid)))
        for _ in range(3):
            message = await asyncio.wait_for(websocket.recv(), timeout=8)
            if isinstance(message, str) and "authSuccess" in message:
                break
        await websocket.send(
            json.dumps(
                {
                    "messageType": "subscribe",
                    "viewName": "FileAiChatThreadsView",
                    "viewHash": THREADS_HASH,
                    "loadType": "initial",
                    "args": {"ownerId": FILE_KEY},
                }
            )
        )
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3)
            except asyncio.TimeoutError:
                break
            if isinstance(message, str) and "denormalizedPendingMutations" in message:
                frames.append(message)

    threads = {}
    for frame in frames:
        try:
            payload = json.loads(frame)
        except json.JSONDecodeError:
            continue
        for mutation in payload.get("mutations", {}).values():
            entity = mutation.get("AiChatThread", {})
            for query in entity.get("queries", {}).values():
                for thread_id, value in (query.get("initial") or {}).items():
                    if isinstance(value, dict):
                        threads[thread_id] = {
                            key: value.get(key)
                            for key in (
                                "privacyMode",
                                "privacy_mode",
                                "title",
                                "userId",
                                "user_id",
                                "threadType",
                            )
                            if key in value
                        }
                    else:
                        threads[thread_id] = {}
    print(f"[{label}] thread_count={len(threads)} ids={sorted(threads)}")
    return threads


async def main():
    cookie_a = load_cookie("ws_cookie_A_new.txt")
    cookie_b = load_cookie("ws_cookie_B_new.txt")
    marker = "privacy-probe-" + uuid.uuid4().hex[:12]
    create_body = {
        "owner_id": FILE_KEY,
        "owner_type": "file",
        "thread_type": "standalone_make",
        "privacy_mode": "user",
        "plan_id": None,
    }
    code, value = rest("POST", "/api/ai_chat/threads", create_body, A_UID, cookie_a)
    meta = value.get("meta", {}) if isinstance(value, dict) else {}
    thread_id = meta.get("thread_id")
    print(
        f"[create private thread] status={code} has_thread_id={bool(thread_id)} "
        f"already_exists={meta.get('already_exists')}"
    )
    if code != 200 or not thread_id:
        print(f"create failed: {value.get('message') if isinstance(value, dict) else value}")
        return

    owner_context = {"owner_id": FILE_KEY, "owner_type": "file"}
    try:
        code, value = rest(
            "PUT",
            f"/api/ai_chat/threads/{thread_id}/title",
            {**owner_context, "title": marker},
            A_UID,
            cookie_a,
        )
        print(f"[set marker title] status={code} success={code == 200}")

        owner_threads = await visible_threads("A owner", A_UID, cookie_a)
        viewer_threads = await visible_threads("B viewer", B_UID, cookie_b)
        anonymous_threads = await visible_threads("anonymous")
        print(
            "[privacy result] "
            f"owner_sees={thread_id in owner_threads} "
            f"viewer_sees={thread_id in viewer_threads} "
            f"anonymous_sees={thread_id in anonymous_threads} "
            f"viewer_marker_visible={viewer_threads.get(thread_id, {}).get('title') == marker}"
        )
    finally:
        code, value = rest(
            "POST",
            f"/api/ai_chat/threads/{thread_id}/delete",
            owner_context,
            A_UID,
            cookie_a,
        )
        print(f"[cleanup private thread] status={code} success={code == 200}")

    print("\n== cross-user thread creation ==")
    for actor_label, uid, cookie in (
        ("A owner baseline", A_UID, cookie_a),
        ("B viewer probe", B_UID, cookie_b),
    ):
        external_session_id = "authz-probe-" + uuid.uuid4().hex
        body = {
            "owner_id": FILE_KEY,
            "owner_type": "file",
            "thread_type": "assistant",
            "privacy_mode": "user",
            "plan_id": None,
            "external_session_id": external_session_id,
        }
        code, value = rest("POST", "/api/ai_chat/threads", body, uid, cookie)
        meta = value.get("meta", {}) if isinstance(value, dict) else {}
        created_thread_id = meta.get("thread_id")
        print(
            f"[{actor_label}] status={code} has_thread_id={bool(created_thread_id)} "
            f"already_exists={meta.get('already_exists')} "
            f"message={value.get('message') if isinstance(value, dict) else None!r}"
        )
        if created_thread_id and not meta.get("already_exists"):
            cleanup_code, _ = rest(
                "POST",
                f"/api/ai_chat/threads/{created_thread_id}/delete",
                {"owner_id": FILE_KEY, "owner_type": "file"},
                uid,
                cookie,
            )
            if cleanup_code != 200 and uid != A_UID:
                cleanup_code, _ = rest(
                    "POST",
                    f"/api/ai_chat/threads/{created_thread_id}/delete",
                    {"owner_id": FILE_KEY, "owner_type": "file"},
                    A_UID,
                    cookie_a,
                )
            print(f"[{actor_label} cleanup] status={cleanup_code}")


asyncio.run(main())
