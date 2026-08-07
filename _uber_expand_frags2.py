"""v2: 完整提取 - 保留换行 + 去注释 + 递归展开 fragment"""
import re, glob, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_comments(text):
    """删除 # 到行尾的注释（GraphQL 注释）"""
    out = []
    for line in text.split('\n'):
        idx = line.find('#')
        if idx >= 0:
            line = line[:idx]
        out.append(line)
    return '\n'.join(out)

def find_closed(text, start):
    """找从 start 处 { 开始的闭合 } 位置"""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1

# 1. 提取所有文档文本（R([...]) 数组拼接）
docs = []
for f in glob.glob('js_m/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    pat = re.compile(r'R\((\[[^\]]*?\])\)', re.S)
    for m in pat.finditer(src):
        try:
            arr = json.loads(m.group(1))
        except Exception:
            continue
        if isinstance(arr, list) and arr and all(isinstance(x, str) for x in arr):
            docs.append(strip_comments(''.join(arr)))

# 2. fragment 定义字典（保留第一个定义）
frag_defs = {}
for d in docs:
    for m in re.finditer(r'fragment\s+([A-Za-z0-9_]+)\s+on\s+[A-Za-z0-9_]+', d):
        name = m.group(1)
        if name in frag_defs:
            continue
        br = d.find('{', m.end())
        end = find_closed(d, br)
        if end > 0:
            frag_defs[name] = d[m.start():end + 1]

# 3. 提取查询 + 递归展开 fragment 引用
def collect(qtext, acc):
    for name in re.findall(r'\.\.\.([A-Za-z0-9_]+)', qtext):
        if name in frag_defs and name not in acc:
            acc.add(name)
            collect(frag_defs[name], acc)
    return acc

def expand(qtext):
    acc = collect(qtext, set())
    return qtext + '\n' + '\n'.join(frag_defs[n] for n in acc)

queries = {}
for d in docs:
    for m in re.finditer(r'\b(query|mutation)\s+([A-Za-z0-9_]+)', d):
        op, name = m.group(1), m.group(2)
        if name in queries:
            continue
        br = d.find('{', m.end())
        end = find_closed(d, br)
        if end > 0:
            qtext = d[m.start():end + 1]
            queries[name] = {'type': op, 'text': expand(qtext)}

print(f'查询 {len(queries)} 个, fragment {len(frag_defs)} 个')
json.dump(queries, open('_uber_queries_full2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for n, info in sorted(queries.items()):
    print(f'  {info["type"]} {n} ({len(info["text"])} chars)')
