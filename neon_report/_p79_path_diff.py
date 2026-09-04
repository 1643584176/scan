# -*- coding: utf-8 -*-
"""bat 类 212 paths vs 公开 OpenAPI 120 paths 差集 -> console 私有端点清单"""
import re, os, json

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()

i_bat = src.find('class bat extends yat')
i_kde = src.find('const Kde')
seg = src[i_bat:i_kde]

paths = set()
for m in re.finditer(r'path:\s*("([^"]+)"|`([^`]+)`)', seg):
    paths.add(m.group(2) or m.group(3))

# 公开 OpenAPI
spec = json.load(open(os.path.join(here, '_openapi_v2_prod.json'), encoding='utf-8'))
pub = set(spec.get('paths', {}).keys())

def norm(x):
    # 模板参数 -> {param}
    import re as _re
    x = _re.sub(r'\$\{encodeURIComponent\([^}]*\)\}', '{}', x)
    x = _re.sub(r'\$\{[^}]*\}', '{}', x)
    return x

norm_pub = {norm(x) for x in pub}
diff = sorted(paths - norm_pub)
out = []
out.append('bat paths: %d, public openapi: %d, diff: %d' % (len(paths), len(pub), len(diff)))
for x in diff:
    out.append(x)
open(os.path.join(here, '_p79_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
