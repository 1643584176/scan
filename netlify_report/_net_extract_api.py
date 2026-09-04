# -*- coding: utf-8 -*-
"""Netlify 接口全量提取 v3:增强方法推断 + 参数/上下文提取"""
import os, re

# ---------- 1. OpenAPI ----------
import yaml
with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)
api_docs = []
for path, ops in spec.get('paths', {}).items():
    for m, op in ops.items():
        if m not in ('get', 'post', 'put', 'delete', 'patch', 'head', 'options'):
            continue
        params = []
        for p in op.get('parameters', []):
            r = 'R' if p.get('required') else 'O'
            params.append('%s:%s' % (p.get('name'), r))
        api_docs.append((m.upper(), path, ','.join(params) or '-',
                         str(op.get('summary', ''))[:60]))
print('OpenAPI endpoints:', len(api_docs))

# ---------- 2. bundle ----------
jsdir = r'D:\scan\netlify_report\_js'
files = {}
for f in os.listdir(jsdir):
    if f.endswith('.js'):
        files[f] = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()

def looks_api(p):
    low = p.lower()
    bad = ['.js', '.css', '.png', '.svg', '.jpg', '.gif', '.woff', '.ttf', '.ico',
           '.html', 'http://', 'https://', 'mailto:', 'javascript:',
           'recaptcha', 'assets/', 'cdn.', '//', '.astro', 'fonts.', 'img.', 'webpack',
           '.map', '.woff2', '.eot', '.mp4', '.webp', '.avif', '.json']
    return not any(b in low for b in bad) and len(p) >= 5

path_pat = re.compile(r'["\'`]((?:/[a-zA-Z0-9_\-${}.]+)+(?:/[a-zA-Z0-9_\-${}.:?=&%]+)*)["\'`]')

def extract(fname, txt):
    hits = []
    for m in path_pat.finditer(txt):
        p = m.group(1)
        if not looks_api(p):
            continue
        if not (p.startswith('/api') or p.startswith('/access-control')
                or p.startswith('/.netlify') or p.startswith('/internal')
                or p.startswith('/private') or '/api/' in p or p.startswith('/v1/')
                or p.startswith('/v2/') or p.startswith('/spark-proxy')):
            continue
        i = m.start()
        ctx = txt[max(0, i - 600): i + 600]
        # 方法:method:"POST" / .post( / axios.post / "POST"
        method = None
        for mm in ['POST', 'GET', 'PUT', 'DELETE', 'PATCH']:
            pats = [
                r'method\s*[:=]\s*["\']%s["\']' % mm,
                r'\.%s\s*\(' % mm.lower(),
                r'["\']%s["\']\s*[,)]' % mm,
            ]
            for pa in pats:
                if re.search(pa, ctx, re.I):
                    method = mm
                    break
            if method:
                break
        # 上下文参数:query 拼接
        q = re.findall(r'[?&]([a-zA-Z_][a-zA-Z0-9_]*)=', p)
        body_keys = []
        # 调用者函数名:最近的前置函数定义
        fn = None
        fm = re.finditer(r'function\s+([a-zA-Z0-9_$]+)|([a-zA-Z0-9_$]+)\s*[:=]\s*(?:async\s*)?\(?[^)]*\)?\s*=>', txt[max(0, i - 1500):i])
        if fm:
            for fm_ in fm:
                fn = fm_.group(1) or fm_.group(2)
        hits.append((method or '?', p, q, fn, ctx))
    return hits

bundle_rows = []
for fname, txt in files.items():
    for h in extract(fname, txt):
        bundle_rows.append((h[0], h[1], h[2], h[3], fname.replace('net_', '').replace('.js', '')))

# 去重合并
merged = {}
for m, p, q, fn, cf in bundle_rows:
    key = (m, p)
    if key not in merged:
        merged[key] = {'q': set(q), 'callers': set(), 'fns': set()}
    merged[key]['q'].update(q)
    merged[key]['callers'].add(cf)
    if fn:
        merged[key]['fns'].add(fn)

# ---------- 2b. 深挖修正(±3000 字符) ----------
def deep_method(path, txt):
    for m in re.finditer(re.escape(path), txt):
        i = m.start()
        ctx = txt[max(0, i - 3000): i + 3000]
        for mm in ['POST', 'GET', 'PUT', 'DELETE', 'PATCH']:
            if re.search(r'method\s*[:=]\s*["\']%s["\']' % mm, ctx, re.I) or \
               re.search(r'\.%s\s*\(' % mm.lower(), ctx) or \
               re.search(r'["\']%s["\']\s*[,)]' % mm, ctx):
                return mm
    return None

for (m, p) in list(merged.keys()):
    if m != '?':
        continue
    for fname, txt in files.items():
        dm = deep_method(p, txt)
        if dm:
            new_key = (dm, p)
            if new_key != (m, p):
                v = merged.pop((m, p))
                if new_key in merged:
                    merged[new_key]['q'].update(v['q'])
                    merged[new_key]['callers'].update(v['callers'])
                    merged[new_key]['fns'].update(v['fns'])
                else:
                    merged[new_key] = v
            break

print('after deep:', len(merged))

# ---------- 3. 输出 ----------
public_paths = {p for _, p, _, _ in api_docs}

def norm(p):
    return re.sub(r'\$\{[^}]+\}', '{}', re.sub(r'\{[^}]+\}', '{}', p)).split('?')[0]

lines = []
lines.append('# Netlify 接口清单(OpenAPI 公开 + bundle 内部)')
lines.append('')
lines.append('> 来源:swagger.yml v%(v)s + app.netlify.com bundle v4 静态分析' % {'v': spec.get('info', {}).get('version', '?')})
lines.append('> 参数列:R=必传 O=可选;caller=调用 bundle;query=URL 查询参数;fn=最近函数')
lines.append('')
lines.append('## A. 公开 API(OpenAPI, %d 条)' % len(api_docs))
lines.append('')
lines.append('| 方法 | 路径 | 参数(名:R/O) | 说明 |')
lines.append('|---|---|---|---|')
for m, p, pa, c in sorted(api_docs):
    lines.append('| %s | `%s` | %s | %s |' % (m, p, pa, c))

lines.append('')
lines.append('## B. bundle 内部端点(%d 条)' % len(merged))
lines.append('')
lines.append('| 方法 | 路径 | query 参数 | 调用方 | 附近函数 |')
lines.append('|---|---|---|---|---|')
for (m, p), v in sorted(merged.items()):
    lines.append('| %s | `%s` | %s | %s | %s |' % (
        m, p, ','.join(sorted(v['q'])) or '-', ','.join(sorted(v['callers'])),
        ','.join(sorted(v['fns'])) or '-'))

lines.append('')
internal = {k: v for k, v in merged.items() if norm(k[1]) not in public_paths}
lines.append('## C. 未出现在 OpenAPI 中的端点(%d 条,重点)' % len(internal))
lines.append('')
lines.append('| 方法 | 路径 | query 参数 | 调用方 | 附近函数 |')
lines.append('|---|---|---|---|---|')
for (m, p), v in sorted(internal.items()):
    lines.append('| %s | `%s` | %s | %s | %s |' % (
        m, p, ','.join(sorted(v['q'])) or '-', ','.join(sorted(v['callers'])),
        ','.join(sorted(v['fns'])) or '-'))

open(r'D:\scan\netlify_report\api-endpoints.md', 'w', encoding='utf-8').write('\n'.join(lines))
print('saved api-endpoints.md lines:', len(lines))
print('public:', len(api_docs), 'bundle-merged:', len(merged), 'internal:', len(internal))
