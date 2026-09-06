# -*- coding: utf-8 -*-
"""Step 2: setup superuser + first website."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

def fetch(path, data=None, timeout=180):
    if data is not None:
        enc = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(BASE + path, data=enc)
    else:
        req = urllib.request.Request(BASE + path)
    try:
        r = op.open(req, timeout=timeout)
        return r.read().decode('utf-8', 'replace'), r.geturl(), r.status
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace'), e.geturl(), e.code

def parse_form(body):
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
        if not nm or nm.group(1) in fields:
            continue
        name = nm.group(1)
        if t.startswith('<input'):
            typ = re.search(r'type="([^"]*)"', t)
            val = re.search(r'value="([^"]*)"', t)
            tval = typ.group(1) if typ else 'text'
            fields[name] = (val.group(1) if val else '') if tval not in ('password', 'submit', 'checkbox') else ''
        else:
            chunk = seg[tag.end():tag.end() + 8000]
            e = chunk.find('</select>')
            chunk = chunk[:e if e > 0 else len(chunk)]
            opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>', chunk)
            sel = re.findall(r'<option[^>]*selected[^>]*value="([^"]*)"', chunk)
            fields[name] = (sel[0] if sel else (opts[0] if opts else ''))
    return action, fields

def alerts(body):
    out = []
    for mm in re.finditer(r'<div class="alert alert-(danger|warning)">(.*?)</div>', body, re.S):
        out.append((mm.group(1), re.sub(r'<[^>]+>|\s+', ' ', mm.group(2)).strip()[:400]))
    return out

if __name__ == '__main__':
    # --- superuser ---
    b, u, s = fetch('index.php?module=Installation&action=setupSuperUser')
    print('GET setupSuperUser', s, len(b), u.split('?')[-1][:60])
    action, fields = parse_form(b)
    if action is None:
        t = re.search(r'<h2>(.*?)</h2>', b, re.S)
        print('  no form; h2:', t.group(1)[:150] if t else '?')
        print('  links:', sorted(set(re.findall(r'action=(\w+)', b)))[:10])
        raise SystemExit(1)
    print('  action:', action[:70], 'fields:', sorted(fields)[:15])
    data = dict(fields)
    data.update({
        'login': 'admin', 'password': 'M@tomoLocalTest!2026',
        'password_bis': 'M@tomoLocalTest!2026',
        'email': 'xxbo+matomo@wearehackerone.com',
    })
    data.pop('submit', None)
    data['submit'] = 'Next'
    b2, u2, s2 = fetch(action, data)
    print('POST setupSuperUser ->', s2, len(b2), u2.split('?')[-1][:70])
    for a in alerts(b2):
        print('  ALERT', a[0], ':', a[1])
    t2 = re.search(r'<h2>(.*?)</h2>', b2, re.S)
    print('  h2:', t2.group(1)[:150] if t2 else 'none')
    open(r'F:\scan\matomo_report\_probes\_su_post.html', 'w', encoding='utf-8').write(b2)
