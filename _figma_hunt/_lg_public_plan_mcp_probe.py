"""Read-only MCP connector visibility test through a public paid-team file."""

import asyncio
import io
import json
import sys

import websockets


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FILE_KEY = "ucha7bf05fJ81CJZVoruo0"
PLAN_IDS = (
    "3fc8b88e-5cb5-4f50-9034-2f341d43ed12",  # Flowbite
    "8c2cd314-b89d-4664-b6dc-6c8ac706665d",  # Figma Demo Org
    "792d795d-82a2-46a2-8aeb-463a32f98f80",  # M3 public file team
)
B_UID = "1667396392129259941"
VIEW_HASH = "d630a1339de765d47ffdff5cac9b2742abcd804f427ed954a5b8b0b90eef68c5"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip().replace("\n", "; ")


def ws_url(uid):
    return (
        "wss://www.figma.com/api/livegraph?pv=1&userId="
        + (uid or "")
        + "&anonUserId=&clientType=web&preload=%7B%7D&requestedProtocolVersion=2"
        + "&clientUrl=https%3A%2F%2Fwww.figma.com%2Fdesign%2F"
        + FILE_KEY
        + "&connectionType=initial&reconnect=0"
    )


def auth(uid):
    return {
        "messageType": "auth",
        "clientType": "web",
        "args": {"userId": uid, "anonymousUserId": None},
        "tags": {"clientType": "web", "clientUrl": f"https://www.figma.com/design/{FILE_KEY}"},
        "clientRequestedVersion": 2,
    }


def summarize(frames):
    result = {"McpServer": {}, "McpClient": {}}
    failures = []
    for frame in frames:
        try:
            value = json.loads(frame)
        except json.JSONDecodeError:
            continue
        if value.get("messageType") == "viewSubscriptionFailed":
            failures.append(value.get("error") or value.get("message"))
        for mutation in value.get("mutations", {}).values():
            for entity_name in result:
                entity = mutation.get(entity_name, {})
                for query in entity.get("queries", {}).values():
                    for entity_id, item in (query.get("initial") or {}).items():
                        if not isinstance(item, dict):
                            result[entity_name][entity_id] = {}
                            continue
                        allowed = (
                            "id",
                            "name",
                            "url",
                            "transport",
                            "publishScope",
                            "publish_scope",
                            "redactedCustomHeaders",
                            "redacted_custom_headers",
                            "mcpServerId",
                            "mcp_server_id",
                            "userId",
                            "user_id",
                        )
                        result[entity_name][entity_id] = {
                            key: item.get(key) for key in allowed if key in item
                        }
    return {
        "server_count": len(result["McpServer"]),
        "client_count": len(result["McpClient"]),
        "servers": result["McpServer"],
        "clients": result["McpClient"],
        "failures": failures,
    }


async def query(label, plan_id, uid=None, cookie=None):
    headers = {"User-Agent": UA, "Origin": "https://www.figma.com"}
    if cookie:
        headers["Cookie"] = cookie
    frames = []
    async with websockets.connect(
        ws_url(uid), additional_headers=headers, max_size=50_000_000, open_timeout=15
    ) as websocket:
        await websocket.send(json.dumps(auth(uid)))
        for _ in range(3):
            message = await asyncio.wait_for(websocket.recv(), timeout=8)
            if isinstance(message, str) and "authSuccess" in message:
                break
        await websocket.send(
            json.dumps(
                {
                    "messageType": "subscribe",
                    "viewName": "McpConnectorsView",
                    "viewHash": VIEW_HASH,
                    "loadType": "initial",
                    "args": {"planId": plan_id},
                }
            )
        )
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3)
            except asyncio.TimeoutError:
                break
            if isinstance(message, str):
                frames.append(message)
    print(f"[{label} / plan={plan_id}] {json.dumps(summarize(frames), ensure_ascii=False)}")


async def main():
    cookie_b = load_cookie("ws_cookie_B_new.txt")
    for plan_id in PLAN_IDS:
        await query("B public-file viewer", plan_id, B_UID, cookie_b)
        await query("anonymous", plan_id)


asyncio.run(main())
