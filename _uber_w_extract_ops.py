"""从 www.uber.com JS 提取 RPC 操作名（request/useQuery 调用）+ 已知 API 端点"""
import re, glob, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ops = set()
# 模式1: request("xxx"
# 模式2: useQuery 包装 (0,X.a)("xxx"
# 模式3: "xxx",{chainWithBootstrap
# 模式4: useMutation 包装
pats = [
    re.compile(r'\.request\(\s*"([A-Za-z0-9_]{3,60})"'),
    re.compile(r'\(0,[A-Za-z0-9_.$]+\)\("([A-Za-z0-9_]{3,60})",'),
    re.compile(r'"([A-Za-z0-9_]{3,60})",\{chainWithBootstrap'),
    re.compile(r'\buseMutation\("([A-Za-z0-9_]{3,60})"'),
]
for f in glob.glob('js_w/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    for pat in pats:
        for m in pat.finditer(src):
            ops.add(m.group(1))

# 模式5: 字符串字面量在 useQuery 变量附近（宽松模式，避免误报只取驼峰+动词开头）
pat5 = re.compile(r'["\']((?:get|fetch|update|create|delete|save|set|submit|request|query|mutate)[A-Z][A-Za-z0-9]{2,60})["\']')
for f in glob.glob('js_w/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    for m in pat5.finditer(src):
        ops.add(m.group(1))

ops = sorted(ops)
print(f'提取到 {len(ops)} 个操作名:')
for o in ops:
    print(f'  {o}')

with open('_uber_w_ops.json', 'w', encoding='utf-8') as f:
    json.dump(ops, f, ensure_ascii=False, indent=1)
print('\n已保存 _uber_w_ops.json')
