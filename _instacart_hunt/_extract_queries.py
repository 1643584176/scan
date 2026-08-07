"""从 instacart JS 恢复 GraphQL 查询文本（gql 模板字符串）"""
import re, glob, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BACKTICK = '`'
QUOTES = ('"', "'", BACKTICK)
pat = re.compile(r'(query|mutation)\s+[A-Za-z0-9_]+\s*(\([^)]*\))?\s*\{', re.S)
found = []
for f in glob.glob('js/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    for m in pat.finditer(src):
        start = m.start()
        if start > 0 and src[start - 1] in QUOTES:
            # 找到完整的查询文本（从引号到对应结束引号，处理转义）
            q = m.group(0)
            found.append((f, q))

print(f'找到 {len(found)} 个查询字面量:')
for f, q in found[:30]:
    print(f'--- {f}')
    print(q[:400].replace('\n', ' '))
    print()
