# -*- coding: utf-8 -*-
"""Full Matomo web installer driver: walk steps until installed."""
import http.cookiejar
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

FILL = {
    'databaseSetup': {
        'host': '127.0.0.1:3307', 'username': 'matomo', 'password': 'matomo',
        'dbname': 'matomo', 'tables_prefix': 'matomo_',
        'adapter': 'MYSQLI', 'schema': 'Mariadb', 'type': 'InnoDB',
    },
    'setupSuperUser': {
        'login': 'admin', 'password': 'M@tomoLocalTest!2026',
        'password_bis': 'M@tomoLocalTest!2026',
        'email': 'xxbo+matomo@wearehackerone.com',
    },
    'firstWebsiteSetup': {
        'siteName': 'Local Test Site', 'url': 'http://127.0.0.1:8080/',
        'timezone': 'UTC', 'ecommerce': '0',
    },
    'reuseTables': {},
}


def get(path):
    r = op.open(BASE + path)
    return r.read().decode('utf-8', 'replace'), r.geturl()


def post(path, data):
    enc = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=enc)
    try:
        r = op.open(req)
        return r.read().decode('utf-8', 'replace'), r.geturl(), r.status
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace'), e.geturl(), e.code


def parse_form(body):
    """Extract first <form>: action + name->(value or '') for inputs/selects/buttons."""
    fm = re.search(r'<form\b[^>]*>', body)
    if not fm:
        return None, None
    m = re.search(r'action="([^"]*)"', fm.group(0))
    action = m.group(1) if m else ''
    if action.startswith('?'):
        action = 'index.php' + action
    end = body.find('</form>', fm.end())
    seg = body[fm.end():end if end > 0 else len(body)]
    fields = {}
    for tag in re.finditer(r'<(?:input|select)\b[^>]*>', seg):
        t = tag.group(0)
        nm = re.search(r'name="([^"]*)"', t)
        if not nm:
            continue
        name = nm.group(1)
        if name in fields:
            continue
        if t.startswith('<input'):
            typ = re.search(r'type="([^"]*)"', t)
            val = re.search(r'value="([^"]*)"', t)
            tval = typ.group(1) if typ else 'text'
            fields[name] = (val.group(1) if val else '') if tval not in ('password', 'submit', 'checkbox') else ''
        else:  # select: chosen default = selected option
            chunk = seg[tag.end():tag.end() + 6000]
            endsel = chunk.find('</select>')
            chunk = chunk[:endsel if endsel > 0 else len(chunk)]
            opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>', chunk)
            sel = re.findall(r'<option[^>]*selected[^>]*value="([^"]*)"', chunk)
            fields[name] = (sel[0] if sel else (opts[0] if opts else ''))
    return action, fields


def err_msg(body):
    """Extract alert-danger / alert-warning text."""
    msgs = []
    for mm in re.finditer(r'<div class="alert alert-(?:danger|warning)">(.*?)</div>', body, re.S):
        txt = re.sub(r'<[^>]+>|\s+', ' ', mm.group(1)).strip()
        if txt:
            msgs.append(txt[:400])
    return msgs


if __name__ == '__main__':
    # steps come from controller order
    steps = ['databaseSetup', 'tablesCreation', 'setupSuperUser',
             'firstWebsiteSetup', 'trackingCode', 'finished']
    cur = 'databaseSetup'
    for i in range(12):
        path = 'index.php?module=Installation&action=' + cur
        body, url = get(path)
        print('GET', cur, '->', len(body), url.split('?')[-1][:60])
        action, fields = parse_form(body)
        if action is None:
            # maybe redirected onward automatically
            t = re.search(r'<title>(.*?)</title>', body, re.S)
            print('  no form; title:', (t.group(1)[:120] if t else 'none'))
            # find next-step link or installed marker
            if 'action=' in body:
                links = sorted(set(re.findall(r'index\.php\?module=Installation&(?:amp;)?action=(\w+)', body)))
                print('  links to:', links[:8])
            break
        print('  form action:', action[:80], 'fields:', sorted(fields)[:20])
        data = dict(fields)
        for k, v in FILL.get(cur, {}).items():
            data[k] = v
        # strip submit buttons that aren't there; keep one
        data.pop('submit', None)
        data['submit'] = 'Next'
        # reuseTables has a special checkbox maybe
        if cur == 'reuseTables':
            data['submit'] = 'Reuse'
        b2, u2, s2 = post(action, data)
        print('POST', cur, '->', s2, len(b2), u2.split('?')[-1][:60])
        for e in err_msg(b2):
            print('  ERR:', e)
        # determine next state
        t2 = re.search(r'<title>(.*?)</title>', b2, re.S)
        print('  title:', (t2.group(1)[:100] if t2 else 'none'))
        # which step are we on now?
        in_url = re.search(r'action=(\w+)', u2 or '')
        nxt = in_url.group(1) if in_url else None
        if nxt and nxt != cur:
            cur = nxt
            print('  -> advanced to', cur)
            continue
        if nxt == cur:
            # same page again => validation failed, show details
            print('  !! still on', cur)
            continue
        # redirect to plain / or ?module=... something else
        if 'installed' in (b2 or '').lower() or 'login' in (b2 or '').lower():
            print('  installed/login marker hit')
            break
        break
