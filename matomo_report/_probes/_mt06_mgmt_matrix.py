# -*- coding: utf-8 -*-
"""Runtime matrix on no-check management methods: admin vs user2 vs user3.
For each method: build minimal params (required ones from signature), call with
idSite=1 (site user2/user3 cannot access). Classify responses."""
import json
import re
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

# param name -> value used when param is REQUIRED (no default in signature)
VAL = {
    'idSite': '1', 'idSites': '1', 'siteId': '1',
    'context': 'web', 'name': 'mt06-x', 'description': '',
    'url': 'http://127.0.0.1:8080/', 'pageUrl': 'http://127.0.0.1:8080/home',
    'pageTitle': 'Home', 'userLogin': 'user3', 'passwordConfirmation': 'User3@LocalTest!2026',
    'pluginName': 'CoreHome', 'languageCode': 'en', 'ipRange': '127.0.0.1',
    'urls': 'index.php?module=API&method=API.getSettings',
    'matchAttribute': 'url', 'pattern': 'x', 'patternType': 'contains',
    'caseSensitive': '0', 'revenue': '0', 'allowMultipleConversionsPerVisit': '0',
    'trigger': 'url', 'expireDate': '', 'expiration': '',
}


def req_params(sig):
    """Parse '$a, int $b = 1, string $c' -> ([required names], [optional names])."""
    req, opt = [], []
    for part in sig.split(','):
        part = part.strip()
        if not part:
            continue
        has_default = '=' in part
        m = re.search(r'\$(\w+)', part)
        if not m:
            continue
        (req if not has_default else opt).append(m.group(1))
    return req, opt


def classify(status, body):
    try:
        j = json.loads(body)
    except Exception:
        return 'HTTP%s-NONJSON' % status if status != 200 else 'DATA-NONJSON'
    if isinstance(j, dict) and j.get('result') == 'error':
        msg = j.get('message', '')
        if 'does not exist or is not available' in msg:
            return 'NOT_AVAILABLE'
        if 'Please specify' in msg or 'must be' in msg or 'Invalid' in msg and 'permission' not in msg.lower():
            return 'PARAM_ERR'
        low = msg.lower()
        if 'access' in low or 'permission' in low or 'not allowed' in low or 'super user' in low:
            return 'ACCESS_DENIED'
        if 'authenticate' in low or 'token' in low or 'login' in low:
            return 'AUTH_ERR'
        return 'ERR:' + msg[:90]
    return 'DATA' if status == 200 else 'HTTP%s' % status


def api(token, plugin, method, req, opt):
    q = dict(module='API', method=plugin + '.' + method, format='json',
             token_auth=token)
    for n in req:
        q[n] = VAL.get(n, '1')
    url = BASE + 'index.php?' + urllib.parse.urlencode(q)
    t0 = time.time()
    reqobj = urllib.request.Request(url)
    try:
        r = urllib.request.urlopen(reqobj, timeout=30)
        body = r.read().decode('utf-8', 'replace')
        return r.status, body, round(time.time() - t0, 1)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        return e.code, body, round(time.time() - t0, 1)
    except Exception as e:
        return 'TIMEOUT', str(e)[:150], round(time.time() - t0, 1)


def main():
    entries = json.load(open('_nocheck_methods.json', encoding='utf-8'))
    callable_ = [x for x in entries if not x['method'].startswith('_')]
    REPORT_PLUGINS = {'Contents', 'CustomDimensions', 'DevicePlugins', 'DevicesDetection',
                      'Events', 'Goals', 'Referrers', 'Resolution', 'Transitions',
                      'UserCountry', 'UserLanguage', 'VisitorInterest', 'VisitsSummary',
                      'VisitTime', 'Actions'}
    mgmt = [x for x in callable_ if x['file'].split('\\')[-2] not in REPORT_PLUGINS]
    WRITE = re.compile(r'^(add|update|delete|create|enable|disable|change|pause|resume|'
                       r'export|import|unlink|link|set|remove|clear)\w*')

    out = []
    for x in sorted(mgmt, key=lambda y: (y['file'].split('\\')[-2], y['method'])):
        plugin = x['file'].split('\\')[-2]
        req, opt = req_params(x['params'])
        row = {'plugin': plugin, 'method': x['method'],
               'kind': 'WRITE' if WRITE.match(x['method']) else 'read',
               'required': req}
        for who, tok in TOKENS.items():
            s, body, dt = api(tok, plugin, x['method'], req, opt)
            cls = classify(s, body)
            row[who] = cls
            row[who + '_body'] = body[:220] if cls in ('DATA',) else \
                (body[:120] if cls.startswith('ERR') or cls == 'ACCESS_DENIED' or cls == 'AUTH_ERR' else '')
        out.append(row)
        print('%-4s %-18s %-42s req=%-30s admin=%-22s user2=%-22s user3=%-22s'
              % (row['kind'], row['plugin'], row['method'], ','.join(req)[:28],
                 row['admin'], row['user2'], row['user3']))
    json.dump(out, open('_mt06_mgmt_matrix.json', 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('TOTAL', len(out))


if __name__ == '__main__':
    main()
