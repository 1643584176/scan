# -*- coding: utf-8 -*-
# r209j: 从 _r202 文件夹响应提取 file keys + 结构（为 asset key 来源）
import io, re, json
raw = io.open('_r202_folder_634606970.txt', encoding='utf-8', errors='replace').read()

# 去 HTTP 头，找 JSON 体
i = raw.find('{', raw.find('\n\n'))
body = raw[i:]
out = []
try:
    j = json.loads(body)
    meta = j.get('meta', {})
    files = meta.get('files') or meta.get('items') or []
    out.append('files count: %d' % len(files))
    for f in files[:25]:
        if isinstance(f, dict):
            out.append('  key=%s name=%s type=%s lib=%s' % (
                f.get('key', '?'), str(f.get('name'))[:40], f.get('editor_type') or f.get('type'),
                str(f.get('library_key'))[:24]))
except Exception as e:
    out.append('json parse fail: %r' % e)
    # fallback regex
    keys = sorted(set(re.findall(r'"key":"([A-Za-z0-9]{10,40})"', body)))
    out.append('regex keys: %d' % len(keys))
    for k in keys[:25]:
        out.append('  ' + k)

io.open('_r209j_files_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:40]))
