# -*- coding: utf-8 -*-
"""Step 3: first website setup -> tracking code -> finished."""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

def fetch(path, data=None, timeout=240):
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
            if tval == 'checkbox':
                fields[name] = val.group(1) if val else '1'
            elif tval == 'submit':
                fields[name] = val.group(1) if val else 'Next'
            else:
                fields[name] = '' if tval == 'password' else (val.group(1) if val else '')
        else:
            chunk = seg[tag.end():tag.end() + 12000]
            e = chunk.find('</select>')
            chunk = chunk[:e if e > 0 else len(chunk)]
            opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>', chunk)
            sel = re.findall(r'<option[^>]*selected[^>]*value="([^"]*)"', chunk)
            fields[name] = (sel[0] if sel else (opts[0] if opts else ''))
    return action, fields

def step(name, fill):
    b, u, s = fetch('index.php?module=Installation&action=' + name)
    print('GET', name, s, len(b), '->', u.split('?')[-1][:60])
    action, fields = parse_form(b)
    if action is None:
        print('  no form (auto-advanced?)')
        return b, u
    data = dict(fields)
    data.update(fill)
    b2, u2, s2 = fetch(action, data)
    print('POST', name, '->', s2, len(b2), 'URL:', u2.split('?')[-1][:70])
    return b2, u2

if __name__ == '__main__':
    # step: first website
    b, u = step('firstWebsiteSetup', {
        'siteName': 'Local Test Site',
        'url': 'http://127.0.0.1:8080/',
        'timezone': 'UTC',
        'ecommerce': '0',
    })
    open(r'F:\scan\matomo_report\_probes\_site_post.html', 'w', encoding='utf-8').write(b)
    nxt = re.search(r'action=(\w+)', u)
    print('current step:', nxt.group(1) if nxt else u[:80])
    # step: trackingCode (usually no form, just link to finished)
    if 'trackingCode' in u or 'finished' in u or 'login' in u.lower():
        b3, u3 = fetch('index.php?module=Installation&action=finished')
        print('GET finished ->', len(b3), u3[:100])
        open(r'F:\scan\matomo_report\_probes\_finish.html', 'w', encoding='utf-8').write(b3)
