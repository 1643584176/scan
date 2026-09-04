# -*- coding: utf-8 -*-
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

s = open(r'D:\scan\neon_report\_neonauth_priv.txt', encoding='utf-8').read().strip().strip('"')
b = bytes.fromhex(s)
target_x = 'T2bvRniQ-dVtriL1EY22pby24AQVsi22hGWV8i4aYtY'
print('blob len:', len(b))

found = False
for off in range(0, len(b) - 31):
    seed = b[off:off + 32]
    try:
        priv = Ed25519PrivateKey.from_private_bytes(seed)
        pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        x = base64.urlsafe_b64encode(pub).rstrip(b'=').decode()
        if x == target_x:
            print('MATCH at offset', off)
            print('seed:', seed.hex())
            open(r'D:\scan\neon_report\_ed_seed.txt', 'w').write(seed.hex())
            found = True
            break
    except Exception:
        pass
if not found:
    print('no match in raw offsets; trying full-blob as DER')
    try:
        from cryptography.hazmat.primitives import serialization as ser
        k = ser.load_der_private_key(b, password=None)
        print('DER ok:', type(k))
    except Exception as e:
        print('DER fail:', e)
