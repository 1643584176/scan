# -*- coding: utf-8 -*-
"""TagManager matrix round 1: admin creates container on site1 (baseline), then
user2/user3 attempt cross-site create/read/delete on site1 object; user2 own-site
create on site2 (control)."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
TOKENS = {
    'admin': 'c3bf071d7f0db740a6f4c60c6affcfd5',
    'user2': '794beeb243443742f0df05b4432c734e',
    'user3': 'bfb52eb146d39b0d40c365a46491f589',
}


def api(tok, method, timeout=45, **params):
    q = dict(params, module='API', method=method, format='json')
    if tok:
        q['token_auth'] = tok
    url = BASE + 'index.php?' + urllib.parse.urlencode(q)
    req = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 'ERR', str(e)[:150]


def show(tag, s, b, n=240):
    print('%-55s | %s | %s' % (tag, s, b.replace('\n', ' ')[:n]))


# 0. plugin state
s, b = api(TOKENS['admin'], 'TagManager.getContainers', idSite=1)
show('admin getContainers(site1) baseline', s, b)

# 1. admin creates container on site1 (baseline write)
s, b = api(TOKENS['admin'], 'TagManager.addContainer', idSite=1, context='web',
           name='s1-base', description='mt06', ignoreGtmDataLayer='0',
           isTagFireLimitAllowedInPreviewMode='1')
show('admin addContainer site1', s, b, 400)
try:
    idc = json.loads(b)['value']
except Exception:
    idc = None
print('idContainer =', idc)

# 2. cross-site attempts on site1's container
if idc:
    for who in ('user2', 'user3'):
        s, b = api(TOKENS[who], 'TagManager.getContainer', idSite=1, idContainer=idc)
        show('%s getContainer(site1 obj)' % who, s, b)
    for who in ('user2', 'user3'):
        s, b = api(TOKENS[who], 'TagManager.addContainer', idSite=1, context='web',
                   name='pwn-by-' + who, description='x')
        show('%s addContainer on site1' % who, s, b)
    for who in ('user2', 'user3'):
        s, b = api(TOKENS[who], 'TagManager.deleteContainer', idSite=1, idContainer=idc)
        show('%s deleteContainer(site1 obj)' % who, s, b)
    for who in ('user2', 'user3'):
        s, b = api(TOKENS[who], 'TagManager.getContainerVersions', idSite=1, idContainer=idc)
        show('%s getContainerVersions(site1 obj)' % who, s, b)
    for who in ('user2', 'user3'):
        s, b = api(TOKENS[who], 'TagManager.exportContainerVersion', idSite=1, idContainer=idc)
        show('%s exportContainerVersion(site1 obj)' % who, s, b, 300)

# 3. user2 control: create on OWN site2 (view-only user -> write should fail)
s, b = api(TOKENS['user2'], 'TagManager.addContainer', idSite=2, context='web',
           name='u2-own', description='x')
show('user2 addContainer on own site2 (view only)', s, b)

# 4. user2 read own site2 containers (view access allows?)
s, b = api(TOKENS['user2'], 'TagManager.getContainers', idSite=2)
show('user2 getContainers site2', s, b)
