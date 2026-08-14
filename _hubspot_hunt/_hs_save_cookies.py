"""保存用户从浏览器 cURL 导出的完整 cookie 集（na1 hublet, base_pccp）"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

cookies = [
    ("__hs_cookie_cat_pref", "1:true_2:true_3:true"),
    ("hubspotutk", "b01f71fc573c1a5b003673c18c1be787"),
    ("hs_c2l", "GL74w2IiGQAQstEnYJ6x-wdM_UMXqONasLDCytczHbg"),
    ("hs_login_email", "base_pccp@protonmail.com"),
    ("_cfuvid", "2dYGVUkJJiA2KepSR3Lh_4UrXydBOM00iYmhZ96LoDE-1786413657.9530716-1.0.1.1-VT6ujSX99vFMp5uXnBhkx.d1wjG0FOky.ZGP12iStho"),
    ("__cf_bm", "K2zB2XiKlsEdclZZgErSUykTbpGj5rphamTNg.lddVI-1786413817.2232695-1.0.1.1-MSjR.gxIj6OqCJhiA42YXK8ReZ_aFAg7.Osbt.xIT0rFJmIYLCBkaF8Iu.YjzqgeokA2loK.Kf8csqEDA7hq5kqNcvnquRrAfcaDbSOwxJKKd5HlsySMdrAcuaPFOxbf"),
    ("hubspotapi", "AAccUftgNFfas8KzbacOac3iCj8An61IkB3cWnvym61xfrS9ALICATfycMvIf0A2U9NkjmP7Nk2ZSSpj0CfVZxUS1gDaww5RqmZzh6ujm68p7HZ-Q3Xlt536piRGs2NP328Syhspk4w-_e8NUUobxOVxzpF1WWRnse3ICnKNgPZwqWZFmTf9Sj0jWSOmo_gAbx5X9s85kbkPxco_5zFQaERWmqA9syPvAiPIssrDqKOnpxZZO-4mDd8H50vdJD8nvSGKejjmImjQ9KoCz7M_7pNfMR2MaiJ6ERzr4GDP_dWoXVJUEB2NaJ7r-mIj10n-rrO8BYrodHtnaJTiUdbzUE1gSmYSd8P8Hw"),
    ("hubspotapi-prefs", "1"),
    ("hubspotapi-csrf", "AAccUfsXTt49SIypGSDI8qlfw_G8iY7BVlKFR8Sml-1p7M0oqM6J3yMrwbJOlT2I3MVLcQdVYmqXj6X7HGcgZ3QrvJHIs6ERFw"),
    ("hubspotapi-lax", "AAccUfvs9yfRZ4YaoyeN4QyY1cJi2j_BHKe_BK5m21rpLJxarOhXySS0ts8U_wveK74bp4W0j2UfPT4CflLqL-fF-M7KmPrMUQ"),
    ("hubspotapi-strict", "AAccUftM0e0lngeR5FigxdnT7XnpUSQUkkLy2Af3yJ5aqreTnn-v8wsFiTQZIU97DVsrsAOhvt4Rlf9ycXQ3YNtex8IE3P86kw"),
    ("hs_login_metadata", "%7B%22isMobileLogin%22%3Afalse%7D"),
    ("csrf.app", "AAccUfsXTt49SIypGSDI8qlfw_G8iY7BVlKFR8Sml-1p7M0oqM6J3yMrwbJOlT2I3MVLcQdVYmqXj6X7HGcgZ3QrvJHIs6ERFw"),
]
CK = "; ".join(f"{k}={v}" for k, v in cookies)
open("hs_cookie_full.txt", "w", encoding="utf-8").write(CK)
print("已保存 hs_cookie_full.txt, cookie 数:", len(cookies), "总长:", len(CK))
