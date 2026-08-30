import urllib.request
for u in ['https://sbx-echo-e29ca9cb-fwvcn8jon-pccp-team.vercel.app/', 'https://sbx-echo-e29ca9cb-pccp-team.vercel.app/']:
    try:
        r = urllib.request.urlopen(u, timeout=12)
        print(u, r.status, r.read()[:300])
    except Exception as e:
        print(u, 'ERR', repr(e)[:150])
