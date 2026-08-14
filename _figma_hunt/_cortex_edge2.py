"""cortex 未测端点认证边界探测:匿名 vs B 登录
端点来源:editor_apis.txt + js_editor/999 chunk 封装定义
只发空 body 探状态码,错误信息即确定性来源
"""
import sys, io, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

ENDPOINTS = [
    ("POST", "/api/cortex/assistant/chat", {}),
    ("POST", "/api/cortex/assistant/find_relevant_ds_assets", {}),
    ("POST", "/api/cortex/assistant/suggest_prompts", {}),
    ("POST", "/api/cortex/dev/openai/chat/completions", {}),
    ("POST", "/api/cortex/dev/openai/embeddings", {}),
    ("GET",  "/api/cortex/dev/stream_cms_collection", None),
    ("GET",  "/api/cortex/dev/stream_object", None),
    ("GET",  "/api/cortex/dev/stream_text", None),
    ("POST", "/api/cortex/dev/testing/ai_chat_blobs_sinatra_api", {}),
    ("POST", "/api/cortex/dev/testing/ai_chat_sinatra_api", {}),
    ("POST", "/api/cortex/dev/request_response_logs/get_request_response_logs", {}),
    ("GET",  "/api/cortex/make/ai_gateway_token", None),
    ("POST", "/api/cortex/community/suggest_resource_tags", {}),
    ("POST", "/api/cortex/figjam/classify_create", {}),
]

def probe(label, cookie=None):
    print(f"\n===== {label} =====")
    for method, path, body in ENDPOINTS:
        hdrs = {"User-Agent": UA, "Accept": "application/json",
                "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
                "X-Figma-Client-Lifecycle-ID": "probe", "Tsid": "probe",
                "X-Referer-Service": "web"}
        data = None
        if body is not None:
            hdrs["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        if cookie:
            hdrs["Cookie"] = cookie
        req = urllib.request.Request("https://www.figma.com" + path, data=data, headers=hdrs, method=method)
        try:
            r = urllib.request.urlopen(req, timeout=12)
            resp = r.read().decode(errors='replace')
            print(f"  {method:4s} {path:62s} {r.status}  {len(resp)}B  {resp[:130]}")
        except urllib.error.HTTPError as e:
            resp = e.read().decode(errors='replace')
            print(f"  {method:4s} {path:62s} {e.code}  {resp[:150]}")
        except Exception as e:
            print(f"  {method:4s} {path:62s} !! {type(e).__name__} {str(e)[:60]}")

probe("匿名")
probe("B 登录态", CK_B)
