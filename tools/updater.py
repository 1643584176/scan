#!/usr/bin/env python3
"""
自动化工具更新模块
可以单独运行: python tools/updater.py
"""
import sys
import os
import subprocess
import concurrent.futures

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

def update_all():
    """更新所有工具"""
    log("检查工具更新...")
    log("这可能需要1-2分钟，请耐心等待...\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_nuclei = executor.submit(update_nuclei)
        future_katana = executor.submit(update_katana)
        future_httpx = executor.submit(update_httpx)
        future_sqlmap = executor.submit(update_sqlmap)
        
        future_nuclei.result()
        future_katana.result()
        future_httpx.result()
        future_sqlmap.result()
    
    log("[OK] 工具更新检查完成\n")

if __name__ == '__main__':
    update_all()
