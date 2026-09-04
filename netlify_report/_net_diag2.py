# -*- coding: utf-8 -*-
"""Netlify:诊断 create deploy 403 错误详情 + 站点 deploy 列表状态"""
import http.client, ssl, gzip, brotli, sys, json, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs='', timeout=20):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path + qs, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

# 1. create 最小 deploy 看 403 body
html = b'<html>x</html>'
body = {'title': 'diag-403', 'files': {'/index.html': hashlib.sha1(html).hexdigest()}}
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', body=body)
print('create:', s, raw[:600].decode('utf-8', 'replace'))

# 2. 站点信息(deploy 配额?)
s, raw = api('/api/v1/sites/%s' % SITE_A)
d = json.loads(raw)
print('site:', s, '| published_deploy:', d.get('published_deploy', {}).get('id') if d.get('published_deploy') else None)
print('build_settings:', json.dumps(d.get('build_settings'))[:200])

# 3. 最近 deploys 状态
s, raw = api('/api/v1/sites/%s/deploys?per_page=10' % SITE_A)
try:
    deploys = json.loads(raw)
    for dp in deploys:
        print('deploy:', dp.get('id', '')[:20], '| state:', dp.get('state'), '| title:', dp.get('title'), '| created:', dp.get('created_at', '')[:19])
except Exception as e:
    print('deploys parse ERR', str(e)[:100], raw[:200])
