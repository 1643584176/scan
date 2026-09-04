# -*- coding: utf-8 -*-
"""对 untracked 文件做内容级凭证模式扫描(只读)。"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ls = [l[3:].strip() for l in open(r'D:\scan\_tmp_untracked_all.txt', encoding='utf-8', errors='replace') if l.startswith('?? ')]
# 去掉 git 引号包裹
def clean(p):
    if p.startswith('"') and p.endswith('"'):
        try:
            p = p.encode().decode('unicode_escape')  # 处理 \357 八进制
            return p.encode('latin-1').decode('utf-8', errors='replace')
        except Exception:
            return p
    return p
ls = [clean(p) for p in ls]

TXT_EXT = {'.py', '.json', '.txt', '.md', '.js', '.ts', '.env', '.sh', '.ps1', '.yaml', '.yml', '.toml', '.xml', '.html', '.csv', '.sql', '.cfg', '.conf', '.ini', '.go', '.rs', '.tsx', '.jsx'}
SKIP_DIR = {'node_modules', '.git', '.venv', '__pycache__', '_js', '_kiwi_ref', '_kiwi_work', '_pg_session_jwt_src', '_gotrue_src', '_pgrepack_src', '_openapi'}

PATS = [
    ('jwt', re.compile(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{8,}')),
    ('bearer', re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._\-]{16,}')),
    ('cred_assign', re.compile(r'''(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|secret[_-]?key|auth[_-]?token|password|passwd|pwd|credential)\s*[=:]\s*['"][A-Za-z0-9_./+\-=]{8,}['"]''')),
    ('setcookie', re.compile(r'(?i)set-cookie\s*:\s*[A-Za-z0-9_\-]{2,}=[^;\r\n]{6,}')),
    ('authz_hdr', re.compile(r'(?i)(?:authorization|x-[\w-]*auth[\w-]*)\s*:\s*(?:basic|bearer)\s+[A-Za-z0-9._\-=]{10,}')),
    ('aws', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('sk_key', re.compile(r'\b(?:sk|pk|rk|vk|whsec|ghp|github_pat_)[A-Za-z0-9_]{20,}\b')),
    ('nf_token', re.compile(r'\b(?:nf|nfp|nf_|nf_|xa|xa2|v1|v2|nft)[A-Za-z0-9_\-]{20,}==?\b')),
]

hits = {}
for rel in ls:
    if not rel or rel.startswith('"'):
        continue
    parts = rel.split('/')
    if any(s in SKIP_DIR for s in parts):
        continue
    fp = os.path.join(r'D:\scan', rel.replace('/', os.sep))
    if not os.path.isfile(fp):
        continue
    ext = os.path.splitext(rel)[1].lower()
    if ext not in TXT_EXT:
        continue
    try:
        if os.path.getsize(fp) > 2 * 1024 * 1024:
            continue
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            data = f.read()
    except Exception:
        continue
    for name, rx in PATS:
        if rx.search(data):
            hits.setdefault(rel, []).append(name)

for rel, names in sorted(hits.items()):
    print(','.join(sorted(set(names))), '|', rel)
print('HIT_COUNT', len(hits))
