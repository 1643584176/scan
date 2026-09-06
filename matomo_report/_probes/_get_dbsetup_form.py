# -*- coding: utf-8 -*-
"""GET databaseSetup page and dump the real form structure."""
import http.cookiejar
import re
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8080/'
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

r = op.open(BASE + 'index.php?module=Installation&action=databaseSetup')
body = r.read().decode('utf-8', 'replace')
open(r'F:\scan\matomo_report\_probes\_dbsetup_get.html', 'w', encoding='utf-8').write(body)
print('len', len(body), 'url', r.geturl())

# extract form element
fm = re.search(r'<form[^>]*>', body)
print('FORM OPEN:', fm.group(0)[:400] if fm else 'NONE')
if fm:
    # capture until </form> (simple heuristic, find closing)
    end = body.find('</form>', fm.end())
    seg = body[fm.end():end]
    for m in re.finditer(r'<(?:input|select|button|textarea)\b[^>]*>', seg):
        tag = m.group(0)
        name = re.search(r'name="([^"]*)"', tag)
        val = re.search(r'value="([^"]*)"', tag)
        opt = ''
        if tag.startswith('<select'):
            # options
            opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>', seg[m.end():m.end()+3000])
            opt = ' opts=' + ','.join(opts[:8])
        print('  ', name.group(1) if name else '?', '=', (val.group(1)[:60] if val else ''), opt, tag[:80])
