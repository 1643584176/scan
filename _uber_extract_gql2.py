"""从 R([...]) 模板数组提取完整 GraphQL 查询"""
import re, glob, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def extract_arrays(src):
    """提取 R(["str","str",...]) 的数组并拼接"""
    out = []
    # 匹配 R([...]) 或类似模板数组
    pat = re.compile(r'R\((\[[^\]]*?\])\)', re.S)
    for m in pat.finditer(src):
        arr_txt = m.group(1)
        try:
            arr = json.loads(arr_txt)
        except Exception:
            continue
        if isinstance(arr, list) and arr and all(isinstance(x, str) for x in arr):
            out.append(''.join(arr))
    return out

queries = {}
fragments = set()
for f in glob.glob('js_m/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    for text in extract_arrays(src):
        # 找查询/mutation 定义
        for m in re.finditer(r'\b(query|mutation)\s+([A-Za-z0-9_]+)\s*(\([^)]*\))?\s*\{', text):
            op, name = m.group(1), m.group(2)
            if name not in queries:
                queries[name] = (op, re.sub(r'\s+', ' ', text).strip())
        # 记录 fragment 名（供分析）
        for m in re.finditer(r'fragment\s+([A-Za-z0-9_]+)', text):
            fragments.add(m.group(1))

print(f'提取到 {len(queries)} 个查询, {len(fragments)} 个 fragment')
print()
for name, (op, q) in sorted(queries.items()):
    print(f'  {op} {name} ({len(q)} chars)')
    print(f'      {q[:200]}')
    print()

with open('_uber_queries.json', 'w', encoding='utf-8') as f:
    json.dump({k: {'type': v[0], 'text': v[1]} for k, v in queries.items()}, f, ensure_ascii=False, indent=1)
print('已保存 _uber_queries.json')
