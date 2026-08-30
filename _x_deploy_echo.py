# -*- coding: utf-8 -*-
"""部署自己的 echo 接收端到 vercel.app (攻击者控制 vhost 的 PoC 接收端)
用 REST API: 上传文件 + 创建部署, 返回 production URL"""
import hashlib, json, sys, time, uuid
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, BASE
import urllib.request

INDEX_JS = r"""module.exports = (req, res) => {
  res.setHeader('content-type', 'application/json');
  res.status(200).end(JSON.stringify({ method: req.method, url: req.url, headers: req.headers }));
};
"""

VERCEL_JSON = r"""{
  "builds": [{ "src": "api/index.js", "use": "@vercel/node" }],
  "routes": [{ "src": "/(.*)", "dest": "/api/index.js" }]
}
"""

def upload_file(content: bytes) -> str:
    sha = hashlib.sha1(content).hexdigest()
    req = urllib.request.Request(BASE + "/v13/files?teamId=%s" % TEAM, method="POST", data=content)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Content-Type", "application/octet-stream")
    req.add_header("x-vercel-digest", sha)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return sha
    except urllib.error.HTTPError as e:
        print('upload err', e.code, e.read().decode()[:200], flush=True)
        return None

name = "sbx-echo-" + uuid.uuid4().hex[:8]
print('project name:', name, flush=True)

# 1. 上传文件
files = {
    "api/index.js": INDEX_JS.encode(),
    "vercel.json": VERCEL_JSON.encode(),
}
shas = {}
for path, content in files.items():
    s = upload_file(content)
    if not s:
        sys.exit(1)
    shas[path] = s
    print('uploaded', path, s[:12], flush=True)

# 2. 创建部署
body = {
    "name": name,
    "project": name,
    "files": [{"file": p, "sha": shas[p]} for p in shas],
    "target": "production",
}
c, r = api("POST", "/v13/deployments?teamId=%s&skipAutoDetectionConfirmation=1" % TEAM, body)
print('deploy create:', c, r[:400], flush=True)
if c != 200:
    sys.exit(1)
d = json.loads(r)
dep_id = d.get("id") or d.get("uid")
url = d.get("url", "")
print('deployment id:', dep_id, 'url:', url, flush=True)

# 3. 轮询 ready
for i in range(30):
    time.sleep(5)
    c, r = api("GET", "/v13/deployments/%s?teamId=%s" % (dep_id, TEAM))
    try:
        st = json.loads(r).get("status")
        print('  poll %d: %s' % (i, st), flush=True)
        if st == "READY":
            break
    except Exception:
        pass

print('DONE url=https://%s' % url, flush=True)
