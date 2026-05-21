#!/usr/bin/env python3
"""
自动化工具更新模块
可以单独运行: python tools/updater.py
"""
import sys
import os
import subprocess
import concurrent.futures
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import log

def update_nuclei():
    """更新 Nuclei"""
    try:
        check_result = subprocess.run(
            ['nuclei', '-update-templates', '-silent'], 
            capture_output=True,
            timeout=60
        )
        
        output = (check_result.stdout + check_result.stderr).decode('utf-8', errors='ignore')
        
        engine_outdated = 'outdated' in output.lower()
        templates_latest = 'latest' in output.lower() or 'up-to-date' in output.lower()
        
        if templates_latest and not engine_outdated:
            return
        
        if engine_outdated:
            subprocess.run(['nuclei', '-update'], capture_output=True, timeout=300)
        else:
            subprocess.run(['nuclei', '-update-templates'], capture_output=True, timeout=300)
    except:
        pass

def update_katana():
    """更新 Katana"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run(
            [sys.executable, os.path.join(project_root, 'tools', 'go_tools.py'), 'install', 'katana'],
            capture_output=True,
            timeout=300
        )
    except:
        pass

def update_httpx():
    """更新 httpx"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run(
            [sys.executable, os.path.join(project_root, 'tools', 'go_tools.py'), 'install', 'httpx'],
            capture_output=True,
            timeout=300
        )
    except:
        pass

def update_sqlmap():
    """更新 SQLMap"""
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'sqlmap'],
            capture_output=True,
            timeout=120
        )
    except:
        pass

def update_subfinder():
    """更新 Subfinder"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run(
            [sys.executable, os.path.join(project_root, 'tools', 'go_tools.py'), 'install', 'subfinder'],
            capture_output=True,
            timeout=300
        )
    except:
        pass

def get_last_update_time():
    """获取上次更新时间"""
    cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.update_cache.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data.get('last_update', ''))
        except:
            pass
    return None

def save_update_time():
    """保存更新时间"""
    cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.update_cache.json')
    try:
        with open(cache_file, 'w') as f:
            json.dump({'last_update': datetime.now().isoformat()}, f)
    except:
        pass

def should_skip_update():
    """判断是否应该跳过更新（24小时内已更新过）"""
    # 可以通过环境变量强制检查更新
    if os.environ.get('FORCE_UPDATE', 'false').lower() == 'true':
        return False
    
    last_update = get_last_update_time()
    if last_update is None:
        return False
    
    # 如果距离上次更新不到24小时，跳过
    return datetime.now() - last_update < timedelta(hours=24)

def update_all():
    """更新所有工具"""
    # 检查是否应该跳过更新
    if should_skip_update():
        log("[INFO] 24小时内已检查过更新，跳过（设置 FORCE_UPDATE=true 强制检查）")
        return
    
    log("检查工具更新...")
    log("这可能需要1-2分钟，请耐心等待...\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_nuclei = executor.submit(update_nuclei)
        future_katana = executor.submit(update_katana)
        future_httpx = executor.submit(update_httpx)
        future_sqlmap = executor.submit(update_sqlmap)
        future_subfinder = executor.submit(update_subfinder)
        
        future_nuclei.result()
        future_katana.result()
        future_httpx.result()
        future_sqlmap.result()
        future_subfinder.result()
    
    # 保存更新时间
    save_update_time()
    log("[OK] 工具更新检查完成\n")

if __name__ == '__main__':
    update_all()
