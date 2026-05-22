#!/usr/bin/env python3
"""
下载 JS 文件到 js 目录
"""
import requests
import os
from urllib.parse import urlparse, unquote

def download_js_files():
    """下载所有 JS 文件"""
    
    # 读取 JS URL 列表
    js_urls_file = os.path.join('js', 'js_urls_clean.txt')
    
    if not os.path.exists(js_urls_file):
        print("未找到 js_urls.txt")
        return
    
    with open(js_urls_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"找到 {len(urls)} 个 JS 文件\n")
    
    # 创建下载目录
    download_dir = os.path.join('js', 'files')
    os.makedirs(download_dir, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    success_count = 0
    fail_count = 0
    
    for url in urls:
        try:
            # 解析文件名
            parsed = urlparse(url)
            path = unquote(parsed.path)
            
            # 提取文件名
            filename = os.path.basename(path)
            
            # 如果文件名包含查询参数，清理一下
            if '?' in filename:
                filename = filename.split('?')[0]
            
            # 确保文件名唯一
            filepath = os.path.join(download_dir, filename)
            counter = 1
            while os.path.exists(filepath):
                name, ext = os.path.splitext(filename)
                filepath = os.path.join(download_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            # 下载文件
            print(f"下载: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                print(f"  ✓ 成功 ({file_size} bytes) -> {filename}\n")
                success_count += 1
            else:
                print(f"  ✗ 失败 (HTTP {response.status_code})\n")
                fail_count += 1
                
        except Exception as e:
            print(f"  ✗ 错误: {e}\n")
            fail_count += 1
    
    print("="*60)
    print(f"下载完成!")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"保存位置: {download_dir}")
    print("="*60)

if __name__ == "__main__":
    download_js_files()
