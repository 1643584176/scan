"""批量验证公开文件 key:从 community 页 HTML 提取候选,用 file_metadata API 过滤出匿名可读文件
输出:公开文件 key 列表
"""
import sys, io, re, json, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
      "Accept": "application/json"}

src = io.open('community_explore2.html', encoding='utf-8', errors='replace').read()
cands = set(re.findall(r'"([A-Za-z0-9]{22})"', src))
# 排除纯数字/hex 和已知 viewName 模式
cands = {k for k in cands if not k.isdigit() and not re.fullmatch(r'[0-9a-f]{22}', k)}
print(f"候选: {len(cands)}")

public = []
checked = 0
for k in sorted(cands):
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            f"https://www.figma.com/api/file_metadata/{k}", headers=UA), timeout=12)
        body = r.read().decode()
        d = json.loads(body)
        checked += 1
        name = d.get("name") or (d.get("file", {}) or {}).get("name")
        if d.get("error") is False or name:
            public.append((k, str(name)[:60]))
            print(f"  ✅ {k}  {name}")
        if checked % 40 == 0:
            time.sleep(1)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"  {k}: HTTP {e.code}")
    except Exception as e:
        print(f"  {k}: {type(e).__name__} {str(e)[:60]}")
    if len(public) >= 30:
        break

json.dump([{"key": k, "name": n} for k, n in public], open("public_file_keys.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n=== 公开文件 {len(public)} 个 → public_file_keys.json ===")
