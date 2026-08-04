import requests, re, sys

h = {'User-Agent': 'Mozilla/5.0'}
base = 'https://ops.wolt.com/static/apps/shell/releases/75419df64a36cc110e3099f660ad406c6a4ec8cb'

r = requests.get(base + '/main.js', headers=h, timeout=20)
txt = r.text
print(f'main.js: {len(txt)} chars')

# Find all quoted key-value pairs with suspicious keys
# Matches: "KEY_NAME": "value"
for m in re.finditer(r'"([A-Z_]{4,40})"\s*:\s*"([^"]{16,200})"', txt):
    key = m.group(1)
    val = m.group(2)
    if any(x in key for x in ['KEY', 'TOKEN', 'SECRET', 'DSN', 'PASS', 'AUTH', 'CRED', 'SENTRY', 'MAPS', 'GOOGLE']):
        print(f'  [{key}] = {val[:100]}')

# Internal wolt domains
urls = set(re.findall(r'https?://[a-z][a-z0-9.-]*\.wolt[a-z0-9.-]*\.(?:com|io|net|fi)[^\s"\'<>]{0,40}', txt))
print(f'\nInternal wolt URLs ({len(urls)}):')
for u in sorted(urls):
    print(f'  {u[:120]}')

# base64 blocks
b64s = re.findall(r'"([A-Za-z0-9+/=]{80,})"', txt)
print(f'\nBase64 blocks >80 chars: {len(b64s)}')
for b in b64s[:3]:
    try:
        import base64
        dec = base64.b64decode(b).decode('utf-8', errors='ignore')
        print(f'  decoded: {dec[:200]}')
    except:
        pass
