# -*- coding: utf-8 -*-
"""prod_app.js webpack chunk map 提取:
webpack runtime 的 chunk 文件名映射(常见形态 __webpack_require__.u 或映射对象)
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()

# 形态1: .u = e => (xxx[e] || e) + "." + {...}[e] + ".js" 或 "assets/xxx."+... 
m = re.search(r'\.u\s*=\s*(?:function\(e\)\{return)?([^;]{0,400}?\.js)', src)
if m:
    print('u-fn:', m.group(1)[:500], flush=True)
# 形态2: 大映射对象 {1:"abc",2:"def"} 后跟 .js 拼接
for pat in [r'\{\d+:"[a-zA-Z0-9]{6,10}"(?:,"?\d+"?:"[a-zA-Z0-9]{6,10}"){5,}\}', r'\{\d+:"[a-zA-Z0-9]+"(?:,\d+:"[a-zA-Z0-9]+"){5,}\}']:
    mm = re.search(pat, src)
    if mm:
        seg = mm.group(0)
        print('map sample len:', len(seg), flush=True)
        print('map head:', seg[:300], flush=True)
        break
# 形态3: jsonp chunk 数组 webpackChunkxxx
i = src.find('self.webpackChunk')
print('webpackChunk idx:', i, flush=True)
if i >= 0:
    print(src[i:i + 300], flush=True)
# 找 ".js" 前缀形态: "assets/"+e+"."+n+".js" 
for m in re.finditer(r'["\'`]([^"\'`]{0,30}?assets/[^"\'`]{0,60}?\.js["\'`])', src):
    print('asset ref:', m.group(1)[:120], flush=True)
