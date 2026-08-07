"""从 m.uber.com JS 提取完整 GraphQL 查询文本"""
import re, glob, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

queries = {}  # name -> (type, text)
for f in glob.glob('js_m/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    # 匹配 query/mutation Name(...) { ... } 的完整文本（含换行/缩进）
    pat = re.compile(r'\b(query|mutation)\s+([A-Za-z0-9_]+)\s*(\([^)]*\))?\s*\{', re.S)
    for m in pat.finditer(src):
        op, name = m.group(1), m.group(2)
        if name in queries:
            continue
        # 从 { 开始匹配大括号
        i = m.start()
        j = m.end() - 1  # 指向 {
        depth = 0
        k = j
        while k < len(src):
            c = src[k]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        q = src[i:k + 1]
        # 清理：取干净文本（去掉多余空白）
        clean = re.sub(r'\s+', ' ', q).strip()
        # 只保留合理的查询（长度 20-8000，包含至少一个字段选择）
        if 20 < len(clean) < 8000 and re.search(r'\{\s*[a-zA-Z_}]', clean):
            queries[name] = (op, clean)

print(f'提取到 {len(queries)} 个查询:')
for name, (op, q) in sorted(queries.items()):
    print(f'  {op} {name} ({len(q)} chars)')

# 保存
with open('_uber_queries.json', 'w', encoding='utf-8') as f:
    json.dump(queries, f, ensure_ascii=False, indent=1)
print()
print('已保存 _uber_queries.json')
