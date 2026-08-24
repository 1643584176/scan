# -*- coding: utf-8 -*-
# createCodeConnectMap 权限探测: B(无权限) vs A(owner) 基线
import sys, json, io
import requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FK = "bv2nMIdFf4u3dESGail4sm"
# 确定性来源: livegraph fileV2.libraryKey (open_editor_filedata.json)
LK = "lk-d12a96bab0f2515990ccf0c32d4ad7d6737ae1317c046dcc45bd44b14b69d3e20b92eb4abc1308e300a534cce3a62827e978ae66ee052d1e60a86fcdf833b2ca"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
CKA = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CKB = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
HDR = {"Origin": "https://www.figma.com", "Referer": f"https://www.figma.com/file/{FK}",
       "User-Agent": UA, "Content-Type": "application/json"}

def create_map(cookie, node_id, extra=None):
    body = {"library_key": LK, "node_id": node_id, "template": "",
            "component_name": "ProbeComponent", "source_path": "src/Probe.tsx",
            "language": "React", "status": "connected", "origin": "mcp_local",
            "entrypoint": ""}
    if extra: body.update(extra)
    r = requests.post("https://www.figma.com/api/code_connect/map",
                      headers={**HDR, "Cookie": cookie}, json=body, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:200]

print("=== 1. B(非协作者) 探测 node_id='0:1' ===")
st, j = create_map(CKB, "0:1")
print(f"B create map: {st} {json.dumps(j, ensure_ascii=False)[:300]}")

print("\n=== 2. A(owner) 基线 同一 node_id ===")
st, j = create_map(CKA, "0:1")
print(f"A create map: {st} {json.dumps(j, ensure_ascii=False)[:300]}")
