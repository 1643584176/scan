"""POST /api/file_proxy/file/{key}/canvas 完整对照矩阵

突破：fv 必须在 query string！POST + fv=101 → 200 fig-kiwij 30752B。
现在对照：
  1. 匿名 vs 登录（文件级权限）
  2. nodes_to_extract 跨文件（对象级遗漏）
  3. nodes_to_extract 乱值/省略
  4. fv 省略/伪造
"""
import json, sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
CK = {c["name"]: c["value"] for c in SESS if c.get("name") and c.get("value")}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
PUBLIC = "bv2nMIdFf4u3dESGail4sm"

CASES = [
    # (name, cookies, file_key, nodes, fv)
    ("登录+私有+本文件节点",      CK,  PRIVATE, "116:2", "101"),
    ("匿名+私有+本文件节点",      None, PRIVATE, "116:2", "101"),
    ("匿名+私有+本文件节点+乱fv", None, PRIVATE, "116:2", "999"),
    ("登录+私有+无节点",          CK,  PRIVATE, None,    "101"),
    ("登录+私有+乱节点",          CK,  PRIVATE, "999999:999", "101"),
    ("登录+私有+公开文件节点",    CK,  PRIVATE, "0:1",   "101"),
    ("登录+私有+混合节点",        CK,  PRIVATE, "116:2,0:1", "101"),
    ("登录+公开+公开文件节点",    CK,  PUBLIC,  "0:1",   "101"),
    ("匿名+公开+公开文件节点",    None, PUBLIC,  "0:1",   "101"),
    ("登录+私有+无fv",            CK,  PRIVATE, "116:2", None),
    ("登录+私有+fv=0",            CK,  PRIVATE, "116:2", "0"),
    ("登录+私有+超大fv",          CK,  PRIVATE, "116:2", "99999999999999999999999"),
]

for name, ck, fk, nodes, fv in CASES:
    q = (f"?nodes_to_extract={nodes}" if nodes else "") + (f"&fv={fv}" if fv else "")
    u = f"https://www.figma.com/api/file_proxy/file/{fk}/canvas{q}"
    try:
        r = requests.post(u, cookies=ck, headers=UA, timeout=25)
        body = r.content
        info = f"{len(body)}B"
        if "json" in r.headers.get("Content-Type", ""):
            info += " " + body[:150].decode(errors="replace").replace("\n", " ")
        else:
            info += " magic=" + body[:12].hex()
        print(f"{name}: {r.status_code} | {info}")
        if r.status_code == 200 and body[:8] != b"<!DOCTYPE":
            fn = f"fp_ok_{name[:6]}_{fk}_{(nodes or 'all').replace(':', '_').replace(',', '+')}.bin"
            open(fn, "wb").write(body)
            print(f"    saved {fn}")
    except Exception as e:
        print(f"{name}: ERR {type(e).__name__} {e}")
