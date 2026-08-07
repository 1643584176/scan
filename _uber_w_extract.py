"""从 www.uber.com JS 提取 GraphQL 查询 + 搜索隐藏字段"""
import re, glob, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. 提取 R([...]) 文档
docs = []
for f in glob.glob('js_w/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    pat = re.compile(r'R\((\[[^\]]*?\])\)', re.S)
    for m in pat.finditer(src):
        try:
            arr = json.loads(m.group(1))
        except Exception:
            continue
        if isinstance(arr, list) and arr and all(isinstance(x, str) for x in arr):
            docs.append(''.join(arr))

# 2. 找查询/mutation + 隐藏字段
queries = {}
hidden = ['userInfo', 'currentUserProfile', 'userProfile', 'stores', 'estimates', 'favorites',
          'remoteConfig', 'countries', 'currencies', 'contact', 'getCurrentUser', 'getProductSuggestions']
print(f'R([...]) 文档数: {len(docs)}')
for d in docs:
    for m in re.finditer(r'\b(query|mutation)\s+([A-Za-z0-9_]+)', d):
        op, name = m.group(1), m.group(2)
        if name not in queries:
            queries[name] = (op, d[:6000])
    for h in hidden:
        if h in d:
            print(f'  隐藏字段 {h} 出现在文档: {d[:120]!r}')

print(f'\n提取到 {len(queries)} 个查询/mutation:')
for n, (op, t) in sorted(queries.items()):
    print(f'  {op} {n} ({len(t)} chars)')

with open('_uber_w_queries.json', 'w', encoding='utf-8') as f:
    json.dump({k: {'type': v[0], 'text': v[1]} for k, v in queries.items()}, f, ensure_ascii=False, indent=1)
print('\n已保存 _uber_w_queries.json')
