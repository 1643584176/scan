"""提取 fragment + 拼接完整查询重测 + 下载 auth.uber.com JS"""
import re, glob, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. 提取全部 fragment
frags = {}
for f in glob.glob('js_m/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    pat = re.compile(r'R\((\[[^\]]*?\])\)', re.S)
    for m in pat.finditer(src):
        try:
            arr = json.loads(m.group(1))
        except Exception:
            continue
        if not (isinstance(arr, list) and arr and all(isinstance(x, str) for x in arr)):
            continue
        text = ''.join(arr)
        for fm in re.finditer(r'fragment\s+([A-Za-z0-9_]+)\s+on\s+[A-Za-z0-9_]+\s*\{', text):
            frags.setdefault(fm.group(1), text)

print(f'fragment 数: {len(frags)}')
for n in frags:
    print(f'  {n}: {len(frags[n])} chars')

# 2. 拼接查询文本（查询 + 引用的 fragments）
queries = json.load(open('_uber_queries.json', encoding='utf-8'))
def expand(qtext):
    out = qtext
    # 找引用的 fragment 名
    for name in re.findall(r'\.\.\.([A-Za-z0-9_]+)', qtext):
        if name in frags and frags[name] not in out:
            out += '\n' + frags[name]
    return out

# 3. 保存扩展后的查询
expanded = {}
for name, info in queries.items():
    expanded[name] = {'type': info['type'], 'text': expand(info['text'])}
json.dump(expanded, open('_uber_queries_full.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('扩展后的查询已保存 _uber_queries_full.json')
