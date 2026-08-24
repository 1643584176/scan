"""Read-only check for MCP connector leakage through a public paid-team file."""

import asyncio
import io
import json
import sys

import websockets


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FILE_KEY = "ucha7bf05fJ81CJZVoruo0"
B_UID = "1667396392129259941"
TEAM_ID = "947922137358580288"
PLAN_RECORD_ID = "3fc8b88e-5cb5-4f50-9034-2f341d43ed12"
VIEW_HASH = "d630a1339de765d47ffdff5cac9b2742abcd804f427ed954a5b8b0b90eef68c5"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip().replace("\n", "; ")


def livegraph_url(uid):
    return (
        "wss://www.figma.com/api/livegraph?pv=1&userId="
        + (uid or "")
        + "&anonUserId=&clientType=web&preload=%7B%7D&requestedProtocolVersion=2"
        + "&clientUrl=https%3A%2F%2Fwww.figma.com%2Fdesign%2F"
        + FILE_KEY
        + "&connectionType=initial&reconnect=0"
    )


def auth_message(uid):
    return {
        "messageType": "auth",
        "clientType": "web",
        "args": {"userId": uid, "anonymousUserId": None},
        "tags": {
            "clientType": "web",
            "clientUrl": f"https://www.figma.com/design/{FILE_KEY}",
        },
        "clientRequestedVersion": 2,
    }


def summarize(frames):
    servers = {}
    clients = {}
    errors = []
    for frame in frames:
        try:
            payload = json.loads(frame)
        except json.JSONDecodeError:
            continue
        if payload.get("messageType") == "viewSubscriptionFailed":
            errors.append(payload.get("error") or payload.get("message"))
        for mutation in payload.get("mutations", {}).values():
            for entity_name, output in (("McpServer", servers), ("McpClient", clients)):
                entity = mutation.get(entity_name, {})
                for query in entity.get("queries", {}).values():
                    for entity_id, value in (query.get("initial") or {}).items():
                        if not isinstance(value, dict):
                            output[entity_id] = {}
                            continue
                        if entity_name == "McpServer":
                            output[entity_id] = {
                                key: value.get(key)
                                for key in (
                                    "name",
                                    "url",
                                    "transport",
                                    "publishScope",
                                    "userId",
                                    "planId",
                                    "redactedCustomHeaders",
                                )
                                if key in value
                            }
                        else:
                            output[entity_id] = {
                                key: value.get(key)
                                for key in ("mcpServerId", "userId", "planId")
                                if key in value
                            }
    return {
        "server_count": len(servers),
        "client_count": len(clients),
        "servers": servers,
        "clients": clients,
        "errors": errors,
    }


async def query(label, plan_id, uid=None, cookie=None):
    headers = {"User-Agent": UA, "Origin": "https://www.figma.com"}
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
    print(f"[{label}] {json.dumps(summarize(frames), ensure_ascii=False)}")


async def main():
    cookie_b = load_cookie("ws_cookie_B_new.txt")
    for plan_label, plan_id in (
        ("team-id", TEAM_ID),
        ("plan-record-id", PLAN_RECORD_ID),
    ):
        await query(f"B / {plan_label}", plan_id, B_UID, cookie_b)
        await query(f"anonymous / {plan_label}", plan_id)


asyncio.run(main())
