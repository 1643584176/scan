"""cortex/internal 高价值接口三视角鉴权探测（匿名/A/B）
空 body 探测仅确认鉴权边界，不猜测参数；对非鉴权错误面再从 JS 提取参数。
"""
import json, sys
import requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_cookies(f):
    return {c["name"]: c["value"] for c in json.load(open(f, encoding="utf-8"))}
A = load_cookies("figma_session.json")
B = load_cookies("figma_session_new.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

# (标签, 方法, 路径, 是否需要 body)
CASES = [
    ("foundry/fs-read-file", "POST", "/api/cortex/foundry/fs-read-file", True),
    ("foundry/files", "GET", "/api/cortex/foundry/files", False),
    ("foundry/debug-sandbox-status", "GET", "/api/cortex/foundry/debug-sandbox-status", False),
    ("dev/request_response_logs", "POST", "/api/cortex/dev/request_response_logs/get_request_response_logs", True),
    ("make/ai_gateway_token", "GET", "/api/cortex/make/ai_gateway_token", False),
    ("make/ai_gateway_token_file", "GET", "/api/cortex/make/ai_gateway_token_file", False),
    ("dev/debug_download_libraries_zip", "POST", "/api/cortex/dev/shared/make_edits/debug_download_libraries_zip", True),
    ("dev/debug_base_configurations", "POST", "/api/cortex/dev/shared/make_edits/debug_base_configurations", True),
    ("mcp/list_tools", "POST", "/api/cortex/mcp/list_tools", True),
    ("mcp/check_auth", "POST", "/api/cortex/mcp/check_auth", True),
    ("shared/mcp_call_tool", "POST", "/api/cortex/shared/mcp_call_tool", True),
    ("dev/openai/chat/completions", "POST", "/api/cortex/dev/openai/chat/completions", True),
    ("figment-proxy/user-support", "POST", "/api/figment-proxy/user-support", True),
    ("figment-proxy/monitor", "GET", "/api/figment-proxy/monitor", False),
    ("integrations/supabase/authorize", "GET", "/api/integrations/supabase/authorize", False),
    ("voice/realtime/session", "POST", "/api/cortex/voice/realtime/session", True),
    ("weave/run", "POST", "/api/cortex/weave/run", True),
    ("weave/inspect", "POST", "/api/cortex/weave/inspect", True),
    ("sinatra/tax_info", "GET", "/api/internal/livegraph/sinatra_resolver/tax_info", False),
    ("pagination/admin_request_dashboard", "GET", "/api/internal/livegraph/pagination_resolver/admin_request_dashboard", False),
]

def probe(method, path, ck, body):
    h = dict(UA)
    if ck:
        h["Cookie"] = "; ".join(f"{k}={v}" for k, v in ck.items())
    try:
        if method == "GET":
            r = requests.get("https://www.figma.com" + path, headers=h, timeout=15)
        else:
            r = requests.post("https://www.figma.com" + path, json=body, headers=h, timeout=15)
        return r.status_code, (r.text[:140] if r.text else "")
    except Exception as e:
        return "ERR", str(e)[:100]

for label, method, path, need_body in CASES:
    body = {} if need_body else None
    results = []
    for v, ck in [("匿", None), ("A", A), ("B", B)]:
        st, txt = probe(method, path, ck, body)
        results.append(f"{v}:{st}")
    # 判定：三种视角状态是否一致
    sts = [r.split(":")[1] for r in results]
    flag = " <<< 视角差异!" if len(set(sts)) > 1 else ""
    print(f"  {label:38s} {' '.join(results)}{flag}")
