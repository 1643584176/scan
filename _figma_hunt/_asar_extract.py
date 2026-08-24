# -*- coding: utf-8 -*-
"""Figma desktop asar 全量解包：提取 renderer/binding 业务代码，排除 node_modules"""
import json, os, sys

SRC = os.path.join(os.path.dirname(__file__), 'Figma-126.8.13-app.asar')
OUT = os.path.join(os.path.dirname(__file__), '_desktop_asar')

data = open(SRC, 'rb').read()
header_len = int.from_bytes(data[4:8], 'little')
header = data[8:8 + header_len]
json_len = int.from_bytes(header[4:8], 'little')
hdr = json.loads(header[8:8 + json_len].decode('utf-8'))
content_offset = 8 + header_len
print(f'header_len={header_len} json_len={json_len} content_offset={content_offset}')

files = []

def walk(node, prefix):
    for name, info in (node.get('files') or {}).items():
        p = os.path.join(prefix, name)
        if 'files' in info:
            walk(info, p)
        else:
            if 'offset' not in info:
                continue  # unpacked 文件，不在 asar 内
            files.append((p, info['size'], int(info['offset'])))

walk(hdr, '')
print(f'total files: {len(files)}')

# 只提取业务相关文件（排除 node_modules 纯库代码）
KEEP_EXT = ('.js', '.json', '.html', '.css', '.map')
kept = []
for p, size, off in files:
    if '/node_modules/' in p.replace('\\', '/'):
        continue
    if p.endswith(KEEP_EXT) or ('binding' in p.lower()) or ('renderer' in p.lower()) or ('preload' in p.lower()):
        kept.append((p, size, off))

print(f'business files: {len(kept)}')
os.makedirs(OUT, exist_ok=True)
for p, size, off in kept:
    target = os.path.join(OUT, p.lstrip('/\\').replace('\\', '/'))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if size > 0:
        with open(target, 'wb') as f:
            f.write(data[content_offset + off: content_offset + off + size])
    else:
        open(target, 'wb').close()

# 列出最大的 20 个业务文件
big = sorted(kept, key=lambda x: -x[1])[:20]
print('--- top 20 ---')
for p, size, off in big:
    print(f'{size:>10} {p}')
