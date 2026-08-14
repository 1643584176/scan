"""HubSpot na2 会话验证 + 基础信息获取（base_pccp, portalId=247013359）"""
import sys, json, requests, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---- 从浏览器导出构建 cookie ----
NEW_HS = "AAccUftV512WVPM_o7JxVhXqLz_AlcJNCGj4JZ87o7mzT5KW8_wxiZFNnwVTGpomqARCdqajn9EtjolvTKA9hes2NyUtorLnhT6vKfcSGz5Y3Nn1MPtLMbi8_Fb2UBYE6U-3f5gTeZAHG6BdO94FXbjA8DklGks3kVKZ4jdzwzUQAwk10z2eMZ7iSk6kbLhIxNMeTxsIDHpMBhDCq3O-6_T1hmeX8h1Wbc97IKzKkYWIRgBRBtqCeexdKXXbNpxCmzD8YbqJLDnTPmBxt_rwUbzuEwUNX1cMfves-9n-MAoXyaXHfXLnMvWj5bRklW8YgN5_eMT3RH6P3mX4E5bAX6cAHZGXdRCdGS8_bHi0_TxVaLNt7kniP0kWxoSbIJaN8wliYpZdXqseQ57yGmdZ1w7Hsy0Qjzdt9_3evILNARKqvFf3xGci1rOuqFd8x0lToEae2abYi4GI6IDdOmDHMwIAaYtbfFJipfFHX7FP391BUB-2scOesHs6nLV29_rnCqqU5EjWNifkT1CTr0oWty_8gNsret7auClekl1z_hdNfnhjg9sN1YX2qkcpYOaAmH-nwmz8Cd1N_4HDBvbq8XqL-ajUtmy5rSTin7LGok0NF3OX7xpQFHqSbAMQWYnw-oDOwYdJxFE-Dl71rYM11TgR1AhEVDLeJTXdsk51DWYsz5KotrUEYoGK8pzyb4gTUYKRDFJJUASA3LODSICclS1_G7YXeXDL-MlWUbicXas5NYat59H0JhlxYr_LFahpKLLlszh0qFkU6-oMR1fyjhFQmUrPomBy8th52jWZ8wDk9SLl4dk1K7QIPSuf3HZ-iBK7k8_zhfYtMOpMaq-ZSwacrZkzcg73UzA5qrPcQ1u0OgwrJzh-48MsK4BvLg6n6tFMN0OGaSOLh-1-7cqkK1dbsYKAUkJloCU43UxMBT6TOZAWzQBneIe1vL04GUBY8nHNcFGIxdy4_V7ShaEPri7rLB1YyVch_uatzij3swrpaO1uatIqGtDNkJJ5MAZpuN4pCTYUrbEZ5bunt504pIiySRoHebeIC78Vjgq2D8WhDrSfuFi3zZzhGh4iLcYAwFV7EF2Y3h6FypoN6KMiLBsRQIagf7xSAF5_LAYsvssoadKcxvLbnColP2eE1MZKmWJPIx0La3OQFRPRnkgUefGT1Em-Xzso69oAOiqbBodYJdAsWMVDM6tpYw3GBk_vfc5QGtGVLVUNKIVtSeaR4cVXdXZtpgtoW1SjIydl0kzV7OdKmwe6wxF6dMfLgRZ5-nA14gYg3xuUATDl8WYukfuJMg4R_wMv7Af5Mdu8GLLtSP7WA12uaBe98lyKgxin5M7Gsg-ZQYViF8OPUmubGLQXtV_aJupcubln1AQbPnsyjmwC0saowi6qCIS2ZLr4KtzS4SvmPsBHhmvl9UFXyaEfLt5kcpS-a1UQuLIojh_IntAokUf7ENgEDt4WQiq0uDOaBHEIfHZo6hNtZdo7Yz-pPbBQ_hJ1-Wfiihair5dR1PJK-lyaC1t8DW7ng2awCTIEcfsXhzIK"
CK = [l for l in open('hs_cookie.txt', encoding='utf-8').read().split('\n') if l.strip() and not l.startswith('#')][0]
CK = re.sub(r'hubspotapi=[^;]+', 'hubspotapi=' + NEW_HS, CK)
open('hs_cookie_na2.txt', 'w', encoding='utf-8').write(CK)
csrf = re.search(r'csrf\.app=([^;]+)', CK).group(1)
print("na2 cookie 已保存 hs_cookie_na2.txt, hubspotapi len:", len(NEW_HS))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Accept": "application/json", "Content-type": "application/json",
     "X-HubSpot-CSRF-hubspotapi": csrf, "Origin": "https://app-na2.hubspot.com",
     "Referer": "https://app-na2.hubspot.com/", "Cookie": CK}

# 1. portal 端点验证
r = requests.get("https://api-na2.hubspot.com/home/v2/api/portal", headers=H, timeout=20)
print("[portal] ->", r.status_code, r.text[:300])

# 2. 用户端点（hubspotapi 解码出 userId 的端点）
for path in ["/home/v2/api/user-info", "/home/v2/api/users/current", "/login-api/v1/user-info"]:
    try:
        rr = requests.get("https://api-na2.hubspot.com" + path, headers=H, timeout=15)
        print(f"[{path}] ->", rr.status_code, rr.text[:200])
    except Exception as e:
        print(f"[{path}] ERR {type(e).__name__}")

# 3. 已知 portal 的 dashboard 数据端点（contacts 数量等）
r3 = requests.get("https://api-na2.hubspot.com/contacts/v1/contacts/vid/0/profile", headers=H, timeout=15)
print("[contacts/v1 vid/0] ->", r3.status_code, r3.text[:300])
