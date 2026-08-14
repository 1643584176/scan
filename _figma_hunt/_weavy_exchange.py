"""weavy code -> id_token 交换(用完整浏览器头过 Cloudflare)
用法: python _weavy_exchange.py <code>
"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
code = sys.argv[1].strip()
body = json.dumps({"code": code, "redirectUri": "https://app.weavy.ai/signin"}).encode()
headers = {
    "Content-Type": "application/json",
    "Origin": "https://app.weavy.ai",
    "Referer": "https://app.weavy.ai/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="151", "Not.A/Brand";v="24", "Microsoft Edge";v="151"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}
req = urllib.request.Request("https://api.weavy.ai/api/v1/auth/figma/oidc/token", data=body, headers=headers)
try:
    r = urllib.request.urlopen(req, timeout=20)
    d = json.loads(r.read().decode())
    print("HTTP", r.status)
    print("keys:", list(d.keys()))
    tok = d.get("id_token", "")
    print("id_token:", tok[:60], "...len", len(tok))
    json.dump(d, open("weavy_idtoken.json", "w"))
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode(errors='replace')[:600])
