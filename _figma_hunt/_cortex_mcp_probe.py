"""cortex MCP 端点探测:eQ 封装要求 X-Figma-* 头族
头构造来源:js_editor/999 eQ 定义(orgId/teamId/fileKey/userId 等)
"""
import sys, io, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
B_UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"      # 已确认的公开文件
B_FILE = ""                              # B 的私有文件 key(暂无)

def call(label, path, body, file_key=None, uid=B_UID, extra=None):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json", "Cookie": CK_B,
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe",
            "X-Referer-Service": "web"}
    if uid:
        hdrs["X-Figma-User-ID"] = uid
    if file_key is not None:
        hdrs["X-Figma-File-Key"] = file_key
    if extra:
        hdrs.update(extra)
    req = urllib.request.Request("https://www.figma.com" + path,
                                 data=json.dumps(body).encode(), headers=hdrs, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=12)
        resp = r.read().decode(errors='replace')
        print(f"[{label}] {r.status}  {len(resp)}B  {resp[:300]}")
    except urllib.error.HTTPError as e:
        resp = e.read().decode(errors='replace')
        print(f"[{label}] {e.code}  {resp[:300]}")
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:80]}")

print("======== cortex MCP 探测(X-Figma-File-Key 头) ========")
# 1. 无 fileKey 头 → 预期 "File key required"(基线)
call("无fileKey头", "/api/cortex/mcp/list_tools", {"id": "figma"})
# 2. 公开文件 key + 无 body → 看 id 校验
call("公开key+空body", "/api/cortex/mcp/list_tools", {}, file_key=PUB_KEY)
# 3. 公开文件 key + id
call("公开key+id=figma", "/api/cortex/mcp/list_tools", {"id": "figma"}, file_key=PUB_KEY)
# 4. 公开文件 key + id=figma-mcp
call("公开key+id=figma-mcp", "/api/cortex/mcp/list_tools", {"id": "figma-mcp"}, file_key=PUB_KEY)
# 5. check_auth 同参
call("check_auth+id=figma", "/api/cortex/mcp/check_auth", {"id": "figma"}, file_key=PUB_KEY)
# 6. 无效 fileKey → 对比错误(文件权限校验?)
call("无效key+id=figma", "/api/cortex/mcp/list_tools", {"id": "figma"}, file_key="0000000000000000000000")
# 7. 无 userId 头(只剩 fileKey)→ 认证边界
call("无uid头", "/api/cortex/mcp/list_tools", {"id": "figma"}, file_key=PUB_KEY, uid=None)
