# -*- coding: utf-8 -*-
try:
    import cryptography
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    print('cryptography', cryptography.__version__)
    pub = bytes.fromhex('3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c')
    sig = bytes.fromhex('92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00')
    msg = bytes(range(1, 129))
    k = Ed25519PublicKey.from_public_bytes(pub)
    k.verify(sig, msg)
    print('TEST2 cryptography verify: OK')
except ImportError as e:
    print('no cryptography:', e)
except Exception as e:
    print('TEST2 cryptography verify FAILED:', e)

try:
    import nacl
    from nacl.signing import VerifyKey
    pub2 = bytes.fromhex('d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a')
    sig2 = bytes.fromhex('e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b')
    VerifyKey(pub2).verify(b'', sig2)
    print('TEST1 nacl verify: OK')
except ImportError:
    print('no nacl')
except Exception as e:
    print('TEST1 nacl verify FAILED:', e)
