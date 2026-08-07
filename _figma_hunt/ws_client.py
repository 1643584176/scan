"""livegraph WS 直连测试：订阅文件数据（基线：自己的文件）
验证 ph 参数有效性 + subscribe 协议
"""
import sys, json, asyncio
import websockets

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def cookie_header():
    cookies = json.load(open(r"D:\scan\_figma_hunt\figma_session.json", encoding="utf-8"))
    parts = []
    for c in cookies:
        if c.get("domain") in ("www.figma.com", "figma.com", ".figma.com", ".www.figma.com"):
            parts.append(f"{c['name']}={c['value']}")
    return "; ".join(parts)

async def main():
    # 参数从捕获的 URL 复用（pr/pt/ph 可能有时效，先试）
    url = ("wss://www.figma.com/api/livegraph"
           "?pv=1&pr=251c5be83e6853e5&pt=1786072093&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds"
           "&userId=1666382703778278399&anonUserId=&clientType=web"
           "&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
           "&preload=%7B%7D&requestedProtocolVersion=2"
           "&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffiles"
           "&connectionType=initial&reconnect=0")
    headers = {"Cookie": cookie_header(), "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    print("连接:", url[:100])
    async with websockets.connect(url, additional_headers=headers, max_size=20_000_000) as ws:
        # 发 auth
        await ws.send(json.dumps({
            "messageType": "auth", "clientType": "web",
            "args": {"userId": "1666382703778278399", "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48",
                     "clientUrl": "https://www.figma.com/files"},
            "clientRequestedVersion": 2}))
        print("已发 auth")
        # 收前几条消息
        for i in range(6):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                print(f"[{i}] {msg[:300]}")
            except asyncio.TimeoutError:
                print(f"[{i}] 超时")
                break
            if i == 0:
                # authSuccess 后发 subscribe
                await ws.send(json.dumps({
                    "messageType": "subscribe",
                    "viewName": "OpenEditorFileData",
                    "viewHash": "3d578d4859a5845c2f037014898cd2e84f17ac3961ec9fa4b7f1d06c302e63c1",
                    "loadType": "initial",
                    "args": {"fileKey": "qzDqStIDJyGbthpKiuvfwg"}}))
                print("已发 subscribe OpenEditorFileData(自己文件)")

asyncio.run(main())
