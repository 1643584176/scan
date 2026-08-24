# -*- coding: utf-8 -*-
"""Compare AI chat visibility for an owner-controlled public Figma Make file."""
import asyncio
import base64
import io
import json
import re
import sys

import websockets

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FILE_KEY = "5zb5YkoxMa09KpqOyuLcHD"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
THREADS_HASH = "3ebe8bcd1ab2477b47769f9f4463b6541a104b6d6762402c7ffadd514bfbe08c"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip().replace("\n", "; ")


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
        "tags": {"clientType": "web", "clientUrl": f"https://www.figma.com/make/{FILE_KEY}"},
        "clientRequestedVersion": 2,
    }


def summarize(frames):
    thread_ids = set()
    message_ids = set()
    part_ids = set()
    content_fields = set()
    decoded_strings = set()
    content_pb_samples = set()
    message_summaries = {}
    part_summaries = {}

    def decode_pb(value):
        if not isinstance(value, str):
            return None
        try:
            raw = base64.b64decode(value + "=" * (-len(value) % 4))
        except (ValueError, base64.binascii.Error):
            return None
        printable = re.findall(rb"[ -~]{3,}", raw)
        return " | ".join(item.decode("utf-8", errors="replace") for item in printable)[:240]

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "contentPb":
                    content_pb_samples.add(f"{type(child).__name__}:{str(child)[:180]}")
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    for frame in frames:
        try:
            payload = json.loads(frame)
        except json.JSONDecodeError:
            continue
        walk(payload)
        encoded = json.dumps(payload, ensure_ascii=False)
        for marker, output in (
            ('"AiChatThread"', thread_ids),
            ('"AiChatMessage"', message_ids),
            ('"AiMessagePart"', part_ids),
        ):
            if marker in encoded:
                output.add(marker.strip('"'))
        if '"contentJson"' in encoded:
            content_fields.add("contentJson")
        if '"contentPb"' in encoded:
            content_fields.add("contentPb")
        for match in re.findall(r'"contentPb":"([A-Za-z0-9+/=_-]+)"', encoded):
            try:
                raw = base64.b64decode(match + "=" * (-len(match) % 4))
            except (ValueError, base64.binascii.Error):
                continue
            for value in re.findall(rb"[ -~]{8,}", raw):
                decoded_strings.add(value.decode("utf-8", errors="replace")[:160])
        mutations = payload.get("mutations", {})
        for mutation in mutations.values():
            for entity_name, bucket in (("AiChatThread", thread_ids), ("AiChatMessage", message_ids), ("AiMessagePart", part_ids)):
                entity = mutation.get(entity_name, {})
                for query in entity.get("queries", {}).values():
                    initial = query.get("initial") or {}
                    bucket.update(initial.keys())
                    for entity_id, value in initial.items():
                        if not isinstance(value, dict):
                            continue
                        if entity_name == "AiChatMessage":
                            message_summaries[entity_id] = {
                                key: value.get(key)
                                for key in ("role", "index", "userId", "threadId")
                                if key in value
                            }
                        elif entity_name == "AiMessagePart":
                            part_summaries[entity_id] = {
                                key: value.get(key)
                                for key in ("partType", "partTypeVersion", "messageId", "partIndex")
                                if key in value
                            }
                            decoded = decode_pb(value.get("contentPb"))
                            if decoded:
                                part_summaries[entity_id]["decoded"] = decoded
    return {
        "bytes": sum(len(frame) for frame in frames),
        "thread_ids": sorted(thread_ids),
        "message_count": len(message_ids),
        "part_count": len(part_ids),
        "content_fields": sorted(content_fields),
        "decoded_strings": sorted(decoded_strings),
        "content_pb_samples": sorted(content_pb_samples),
        "messages": message_summaries,
        "parts": part_summaries,
    }


async def query(label, uid=None, cookie=None):
    headers = {"User-Agent": UA, "Origin": "https://www.figma.com"}
    if cookie:
        headers["Cookie"] = cookie
    frames = []
    async with websockets.connect(
        livegraph_url(uid), additional_headers=headers, max_size=50_000_000, open_timeout=15
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
    print(label, json.dumps(summarize(frames), ensure_ascii=False))


async def main():
    await query("A-owner", A_UID, load_cookie("ws_cookie_A_new.txt"))
    await query("B-viewer", B_UID, load_cookie("ws_cookie_B_new.txt"))
    await query("anonymous")


asyncio.run(main())
