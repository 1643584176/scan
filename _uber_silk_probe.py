"""基于用户抓包的确定性请求格式，验证 auth.uber.com silk-screen 服务端校验强度
测试点：
  T1 无 deviceData 提交 INITIAL        -> deviceData 是否必填
  T2 随机 deviceData 提交 INITIAL      -> deviceData 是否校验内容
  T3 伪造 inAuthSessionID 调 prepare-field -> session 是否服务端绑定
  T4 伪造 inAuthSessionID 提交 OTP     -> 错误类型区分 session 校验
  T5 nextURL 篡改为外域提交 INITIAL    -> open redirect 信号
"""
import sys, json, uuid, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://cn-geo1.uber.com/rt/silk-screen"
EMAIL = "test.probe.2026.insta@gmail.com"

H = {
    "Content-Type": "application/json",
    "Origin": "https://auth.uber.com",
    "Referer": "https://auth.uber.com/v2/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

def post(path, body):
    try:
        r = requests.post(f"{BASE}{path}", json=body, headers=H, timeout=15)
        return r.status_code, r.text[:600]
    except Exception as e:
        return -1, str(e)[:200]

def fake_session():
    return f"{uuid.uuid4()}_{uuid.uuid4()}"

def form_answer(extra=None):
    fa = {
        "flowType": "INITIAL", "standardFlow": True, "accountManagementFlow": False,
        "daffFlow": False,
        "productConstraints": {"isEligibleForWebOTPAutofill": False, "uslFELibVersion": "",
                               "uslMobileLibVersion": "", "isWhatsAppAvailable": False,
                               "isPublicKeyCredentialSupported": True, "isFacebookAvailable": False,
                               "isRakutenAvailable": False, "isKakaoAvailable": False},
        "additionalParams": {"isEmailUpdatePostAuth": False},
        "nextURL": "https://m.uber.com", "uslURL": "https://auth.uber.com/v2/",
        "authDomain": "auth.uber.com",
        "screenAnswers": [{"screenType": "PHONE_NUMBER_INITIAL", "eventType": "TypeInputEmail",
                           "fieldAnswers": [{"fieldType": "EMAIL_ADDRESS", "emailAddress": EMAIL}]}],
    }
    if extra:
        fa.update(extra)
    return fa

def wrap(fa, session=""):
    return {"formContainerAnswer": {"inAuthSessionID": session, "formAnswer": fa}}

print("=== T1: 无 deviceData 提交 INITIAL ===")
st, body = post("/submit-form", wrap(form_answer()))
print(st, body)

print("\n=== T2: 随机 deviceData('AAAA') 提交 INITIAL ===")
st, body = post("/submit-form", wrap(form_answer({"deviceData": "AAAA"})))
print(st, body)

print("\n=== T3: 伪造 inAuthSessionID 调 prepare-field ===")
sid = fake_session()
st, body = post("/prepare-field", {"request": {"flowType": "SIGN_UP", "inAuthSessionID": sid,
                                               "eventType": "TypeEmailOTP", "fieldType": "EMAIL_OTP_CODE"}})
print(f"session={sid}")
print(st, body)

print("\n=== T4: 伪造 inAuthSessionID 提交 OTP ===")
sid = fake_session()
body4 = {"formContainerAnswer": {"inAuthSessionID": sid,
    "formAnswer": {"flowType": "SIGN_UP", "standardFlow": True, "accountManagementFlow": False,
                   "daffFlow": False,
                   "productConstraints": {"isEligibleForWebOTPAutofill": False, "uslFELibVersion": "",
                                          "uslMobileLibVersion": "", "isWhatsAppAvailable": False,
                                          "isPublicKeyCredentialSupported": True,
                                          "isFacebookAvailable": False, "isRakutenAvailable": False,
                                          "isKakaoAvailable": False},
                   "additionalParams": {"isEmailUpdatePostAuth": False},
                   "deviceData": "AAAA",
                   "nextURL": "https://m.uber.com", "uslURL": "https://auth.uber.com/v2/",
                   "authDomain": "auth.uber.com",
                   "screenAnswers": [{"screenType": "EMAIL_OTP_CODE", "eventType": "TypeEmailOTP",
                                      "fieldAnswers": [{"fieldType": "EMAIL_OTP_CODE", "": "0000"}]}]}}}
print(f"session={sid}")
st, body = post("/submit-form", body4)
print(st, body)

print("\n=== T5: nextURL 篡改为外域 提交 INITIAL ===")
st, body = post("/submit-form", wrap(form_answer({"nextURL": "https://evil.example.com"})))
print(st, body)
