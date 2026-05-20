#!/usr/bin/env python3
"""
JavaScript 文件分析工具。
用法: python js_analyzer.py <目标URL或all_urls.txt> [输出目录]
功能：
1. 下载并分析 JS 文件
2. 提取 API 端点
3. 提取硬编码的 URL
4. 发现潜在的敏感信息
"""

import os
import sys
import re
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime

def log(message):
    """输出带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

class JSAnalyzer:
    def __init__(self):
        self.js_files = []
        self.extracted_urls = []
        self.extracted_endpoints = []
        self.potential_secrets = []
        
    def find_js_files(self, urls_file):
        """从 URL 列表中找出所有 JS 文件"""
        if not os.path.exists(urls_file):
            log(f"[ERROR] 文件不存在: {urls_file}")
            return False
        
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        # 过滤出 JS 文件
        for url in urls:
            if url.endswith('.js') or '/static/' in url.lower():
                parsed = urlparse(url)
                if parsed.path.endswith('.js'):
                    self.js_files.append(url)
        
        log(f"[INFO] 发现 {len(self.js_files)} 个 JS 文件")
        return True
    
    def download_and_analyze(self, base_url, output_dir):
        """下载并分析 JS 文件"""
        log("[INFO] 开始分析 JS 文件...")
        
        # 如果没有找到 JS 文件，尝试从主页查找
        if not self.js_files:
            log("[INFO] 尝试从主页提取 JS 文件...")
            try:
                resp = requests.get(base_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                })
                
                # 提取 script 标签中的 src
                script_pattern = r'<script[^>]+src=["\']([^"\']+)["\']'
                scripts = re.findall(script_pattern, resp.text)
                
                for script_src in scripts:
                    if script_src.endswith('.js'):
                        full_url = urljoin(base_url, script_src)
                        self.js_files.append(full_url)
                
                log(f"[INFO] 从主页找到 {len(self.js_files)} 个 JS 文件")
            except Exception as e:
                log(f"[WARN] 无法访问主页: {e}")
                return
        
        # 分析每个 JS 文件
        for i, js_url in enumerate(self.js_files[:10], 1):  # 限制分析前10个
            log(f"[INFO] [{i}/{min(len(self.js_files), 10)}] 分析: {js_url[:80]}...")
            
            try:
                resp = requests.get(js_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                })
                
                if resp.status_code == 200:
                    content = resp.text
                    self.analyze_content(content, js_url)
            except Exception as e:
                log(f"[WARN] 无法下载 {js_url}: {e}")
        
        log(f"[OK] 分析完成!")
        log(f"   - 提取 URL: {len(self.extracted_urls)} 个")
        log(f"   - 提取端点: {len(self.extracted_endpoints)} 个")
        log(f"   - 潜在秘密: {len(self.potential_secrets)} 个")
    
    def analyze_content(self, content, source_url):
        """分析 JS 内容"""
        # 1. 提取 URL/API 端点
        url_patterns = [
            r'["\'](https?://[^"\']+)["\']',  # 完整 URL
            r'["\'](/api/[^"\']+)["\']',       # API 路径
            r'["\'](/v\d+/[^"\']+)["\']',      # 版本化 API
            r'fetch\(["\']([^"\']+)["\']',     # fetch 调用
            r'axios\.(get|post)\(["\']([^"\']+)["\']',  # axios 调用
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[-1]  # 取最后一个组
                
                # 清理和规范化 URL
                match = match.strip()
                if match and len(match) > 5 and len(match) < 200:
                    if match.startswith('http'):
                        self.extracted_urls.append(match)
                    elif match.startswith('/'):
                        # 相对路径，转换为绝对路径
                        parsed = urlparse(source_url)
                        full_url = f"{parsed.scheme}://{parsed.netloc}{match}"
                        self.extracted_urls.append(full_url)
                        self.extracted_endpoints.append(match)
        
        # 2. 提取潜在的密钥/令牌
        secret_patterns = [
            r'(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'(?:token|secret)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'(?:password|passwd)["\']?\s*[:=]\s*["\']([^"\']{5,})["\']',
        ]
        
        for pattern in secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                self.potential_secrets.append({
                    'type': 'potential_secret',
                    'value': match[:50] + '...',  # 只显示前50个字符
                    'source': source_url
                })
    
    def save_results(self, output_dir):
        """保存分析结果"""
        # 使用固定文件名，每次覆盖
        
        # 保存提取的 URL
        urls_file = os.path.join(output_dir, 'js_extracted_urls.txt')
        with open(urls_file, 'w', encoding='utf-8') as f:
            for url in set(self.extracted_urls):
                f.write(url + '\n')
        
        log(f"[INFO] 提取的 URL: {urls_file}")
        
        # 保存端点
        endpoints_file = os.path.join(output_dir, 'js_endpoints.txt')
        with open(endpoints_file, 'w', encoding='utf-8') as f:
            for endpoint in set(self.extracted_endpoints):
                f.write(endpoint + '\n')
        
        log(f"[INFO] 提取的端点: {endpoints_file}")
        
        # 保存潜在秘密
        secrets_file = os.path.join(output_dir, 'js_secrets.json')
        import json
        with open(secrets_file, 'w', encoding='utf-8') as f:
            json.dump(self.potential_secrets, f, indent=2, ensure_ascii=False)
        
        log(f"[INFO] 潜在秘密: {secrets_file}")
        
        return urls_file, endpoints_file, secrets_file


def main():
    if len(sys.argv) < 2:
        print("用法: python js_analyzer.py <目标URL或all_urls.txt> [输出目录]")
        print("\n示例:")
        print("  python js_analyzer.py https://example.com @example.com_bounty")
        print("  python js_analyzer.py @example.com_bounty/all_urls.txt @example.com_bounty")
        sys.exit(1)
    
    target = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    analyzer = JSAnalyzer()
    
    # 判断是 URL 还是文件
    base_url = None
    if os.path.exists(target):
        # 从文件加载 URL
        log(f"[INFO] 从文件加载 URL 列表: {target}")
        analyzer.find_js_files(target)
        
        # 从 all_urls.txt 中提取基础 URL（第一个 URL）
        try:
            with open(target, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
                if urls:
                    # 取第一个 URL 作为 base_url
                    from urllib.parse import urlparse
                    parsed = urlparse(urls[0])
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    log(f"[INFO] 使用基础 URL: {base_url}")
        except Exception as e:
            log(f"[WARN] 无法读取基础 URL: {e}")
    else:
        # 单个 URL
        base_url = target
        analyzer.js_files = []
    
    # 下载并分析
    analyzer.download_and_analyze(base_url or 'https://example.com', output_dir)
    
    # 保存结果
    analyzer.save_results(output_dir)
    
    log("[OK] JS 分析完成!")


if __name__ == "__main__":
    main()
