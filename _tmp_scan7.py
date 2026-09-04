# -*- coding: utf-8 -*-
"""补扫: AWS/会话凭证键、大写 PWD/PASS 赋值、import creds 模块引用。"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ls = [l[3:].strip() for l in open(r'D:\scan\_tmp_untracked_all.txt', encoding='utf-8', errors='replace') if l.startswith('?? ')]
def clean(p):
    if p.startswith('"') and p.endswith('"'):
        try:
            p = p.encode().decode('unicode_escape')
            return p.encode('latin-1').decode('utf-8', errors='replace')
        except Exception:
            return p
    return p
ls = [clean(p) for p in ls]

TXT_EXT = {'.py', '.json', '.txt', '.md', '.js', '.env', '.sh', '.ps1', '.yaml', '.yml', '.toml', '.xml', '.html', '.csv', '.sql', '.cfg', '.conf', '.ini', '.go', '.rs'}
SKIP = {'node_modules', '.git', '.venv', '__pycache__', '_js', '_sb_js', '_kiwi_ref', '_kiwi_work', '_pg_session_jwt_src', '_gotrue_src', '_pgrepack_src', '_openapi'}

PATS = [
    ('aws_key_id', re.compile(r'["\']?AWS_ACCESS_KEY_ID["\']?\s*[:=]\s*["\'][^"\']{15,}["\']')),
    ('aws_sec', re.compile(r'["\']?AWS_SECRET_ACCESS_KEY["\']?\s*[:=]\s*["\'][^"\']{15,}["\']')),
    ('aws_sess', re.compile(r'["\']?AWS_SESSION_TOKEN["\']?\s*[:=]\s*["\'][^"\']{30,}["\']')),
    ('pwd_assign', re.compile(r"""(?im)^\s*(?:pwd|pass|password|passwd|pgpwd|dbpwd|secret|apikey|token)\s*=\s*['"][^'"]{6,}['"]""")),
    ('import_creds', re.compile(r'(?im)^\s*(?:from|import)\s+_?(?:net_creds|figma_creds|neon_creds|supabase_creds|aic_creds)')),
]
for rel in sorted(ls):
    if not rel:
        continue
    parts = rel.split('/')
    if any(s in SKIP for s in parts):
        continue
    fp = os.path.join(r'D:\scan', rel.replace('/', os.sep))
    if not os.path.isfile(fp):
        continue
    ext = os.path.splitext(rel)[1].lower()
    if ext not in TXT_EXT:
        continue
    try:
        if os.path.getsize(fp) > 3 * 1024 * 1024:
            continue
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            data = f.read()
    except Exception:
        continue
    for name, rx in PATS:
        m = rx.search(data)
        if m:
            print(name, '|', rel, '|', m.group(0)[:80].replace('\n', ' '))
            break
