import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

p = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/42dcb5db/42dcb5db.jsonl'
raw = open(p, encoding='utf-8').read()

i = raw.find("L1 xfrom")
print('=== L1 xfrom script @', i)
print(raw[i:i + 800].replace('\\n', '\n').replace('\\"', '"'))
print()

i = raw.find("O2 xbind join")
print('=== O2 xbind join script @', i)
print(raw[i - 250:i + 600].replace('\\n', '\n').replace('\\"', '"'))
print()

# O2 xbind join result
i2 = raw.find("O2 xbind join (")
print('=== O2 xbind result @', i2)
print(raw[i2:i2 + 400].replace('\\n', '\n').replace('\\"', '"'))
print()

# search for any "O2 ref-out" or surrounding O-series judgments about from rebinding
i3 = raw.find("重绑定")
while i3 != -1 and i3 < len(raw):
    seg = raw[max(0, i3 - 300):i3 + 200].replace('\\n', '\n').replace('\\"', '"')
    print('=== 重绑定 ctx @', i3)
    print(seg)
    print()
    i3 = raw.find("重绑定", i3 + 1)
    if i3 > 1300000:
        break
