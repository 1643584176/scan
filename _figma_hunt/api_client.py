"""Figma API 客户端：从 figma_session.json 加载 session，封装已登录请求
用法: python api_client.py <path>  -> 测试 /api/user
      from api_client import client   -> 复用
"""
import json, sys, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESSION_FILE = r"D:\scan\_figma_hunt\figma_session.json"
BASE = "https://www.figma.com"

def load_cookies(path=SESSION_FILE):
    return json.load(open(path, encoding="utf-8"))

def build_client(path=SESSION_FILE):
    s = requests.Session()
    for c in load_cookies(path):
        if c.get("domain") in ("www.figma.com", "figma.com", ".figma.com", ".www.figma.com"):
            s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path", "/"))
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://www.figma.com",
        "Referer": "https://www.figma.com/",
    })
    return s

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else SESSION_FILE
    s = build_client(path)
    r = s.get(f"{BASE}/api/user", timeout=15)
    print("status:", r.status_code)
    print("headers:", dict(list(r.headers.items())[:8]))
    print("body:", r.text[:500])
