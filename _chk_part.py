# 本地验证 J287 分块逻辑
import base64, re

src = open('exp_j287.py', encoding='utf-8').read()
m = re.search(r'PAYLOAD = r\'\'\'(.*?)\'\'\'', src, re.S)
p = m.group(1)
data = p.encode()
print('PAYLOAD len:', len(data))
b64 = base64.b64encode(data).decode()
print('B64 len:', len(b64))
parts = [b64[i:i + 3500] for i in range(0, len(b64), 3500)]
print('num parts:', len(parts))
print('part0 head:', parts[0][:40])
print('part0 decoded head:', base64.b64decode(parts[0])[:60])
# 模拟 upload_file 生成的 code
for i, part in enumerate(parts):
    mode = 'wb' if i == 0 else 'ab'
    code = "import base64;open(%r,%r).write(base64.b64decode(%r))" % ("/tmp/rec.py", mode, part)
    print('part%d code len: %d, has-quote: %s, has-backslash: %s' % (i, len(code), "'" in code, '\\' in code))
