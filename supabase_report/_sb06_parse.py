# -*- coding: utf-8 -*-
"""公开侦察4: buildManifest 解析 -> 下载关键页面 chunk(sql/database/settings)
格式: self.__BUILD_MANIFEST={...}; self.__BUILD_MANIFEST_CB
"""
import re, os, json, http.client, ssl

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
ASSET = 'frontend-assets.supabase.com'
PREFIX = '/studio/e25c0e83dff6/_next/static/'

txt = open(os.path.join(here, '_sb05_buildManifest.js'), encoding='utf-8', errors='replace').read()
m = re.search(r'=(\{.*?\})\s*;?\s*self\.__BUILD_MANIFEST_CB', txt, re.S)
body = m.group(1) if m else txt
print('manifest body len:', len(body), flush=True)
# 探测 JSON 结构(可能非标准 JSON: 单引号/无引号 key)
try:
    data = json.loads(body)
    print('json ok, keys:', len(data), flush=True)
except Exception as e:
    print('not pure json:', e, flush=True)
    data = None

# 结构探测: 前 300 字符
print('head:', body[:400], flush=True)
