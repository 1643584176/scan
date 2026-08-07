"""抓取 livegraph WebSocket 真实流量（查询格式的确定性来源）
注入已登录 cookies -> 打开 files 页面 -> 监听 WS 帧 -> 保存
"""
import sys, json, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

cookies = json.load(open(r"D:\scan\_figma_hunt\figma_session.json", encoding="utf-8"))
ws_messages = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    def on_ws(ws):
        print("WS 连接:", ws.url[:120])
        def on_sent(f):
            if f:
                ws_messages.append({"dir": "SENT", "data": f})
        def on_recv(f):
            if f:
                ws_messages.append({"dir": "RECV", "data": f})
        ws.on("framesent", on_sent)
        ws.on("framereceived", on_recv)

    page.on("websocket", on_ws)
    page.goto(
        "https://www.figma.com/files/team/1666382706663462213/recents-and-sharing?fuid=1666382703778278399",
        wait_until="domcontentloaded", timeout=60000)
    time.sleep(20)  # 等 WS 连接和初始订阅

    json.dump(ws_messages, open(r"D:\scan\_figma_hunt\ws_traffic.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("WS 消息数:", len(ws_messages))
    browser.close()
