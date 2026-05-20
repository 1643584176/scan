#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JS 文件敏感信息扫描器
用于检测 JavaScript 文件中的潜在安全问题
支持从目标URL自动提取和分析JS文件
"""

import re
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class JSAnalyzer:
    def __init__(self):
        # 敏感信息模式
        self.patterns = {
            'API Keys/Tokens': [
                r'\b(api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']{10,}["\']',
                r'\b(access[_-]?token|auth[_-]?token)\s*[=:]\s*["\'][^"\']{10,}["\']',
                r'\b(secret|secret[_-]?key)\s*[=:]\s*["\'][^"\']{8,}["\']',
                r'\b(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']',
                r'\b(credentials?)\s*[=:]\s*["\'][^"\']+["\']',
            ],
            '内部端点/URL': [
                r'https?://[a-zA-Z0-9\-\.]*(staging|dev|test|internal|admin|local)[a-zA-Z0-9\-\.]*\.[a-z]+',
                r'https?://[a-zA-Z0-9\-\.]*\.(syfe|sembcorp|euroland|azure|amazonaws)\.[a-z]+[^\s"\']*',
            ],
            '注释中的敏感信息': [
                r'//.*(?:todo|fixme|hack|xxx|debug|temp|test)',
                r'/\*[\s\S]*?(?:todo|fixme|hack|xxx|debug|temp|test)[\s\S]*?\*/',
            ],
            '危险函数调用': [
                r'\.innerHTML\s*=',
                r'\.outerHTML\s*=',
                r'document\.write\s*\(',
                r'\beval\s*\(',
                r'setTimeout\s*\(\s*["\']',
                r'setInterval\s*\(\s*["\']',
                r'new\s+Function\s*\(',
            ],
            '硬编码凭证': [
                r'["\'](?:bearer|basic|token)\s+[A-Za-z0-9+/=]{20,}["\']',
                r'Authorization\s*:\s*["\']Bearer\s+[A-Za-z0-9\._\-]+["\']',
            ],
            '第三方服务': [
                r'(?:google-analytics|googletagmanager|gtag)\.(?:com|js)',
                r'(?:facebook|fb)\.com.*(?:pixel|sdk)',
                r'(?:hotjar|intercom|zendesk|crisp)\.(?:com|js)',
            ],
            'API端点': [
                r'["\'](/api/[^"\']+)["\']',
                r'["\'](/v\d+/[^"\']+)["\']',
                r'["\'](/graphql[^"\']*)["\']',
                r'fetch\(["\']([^"\']+)["\']',
                r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']',
            ],
        }
        
        self.findings = []
        self.base_url = ''
        
    def extract_js_from_url(self, url):
        """从网页提取所有JS文件链接"""
        print(f"\n{'='*80}")
        print(f"正在分析网站: {url}")
        print(f"{'='*80}\n")
        
        self.base_url = url
        js_files = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 提取script标签
            for script in soup.find_all('script', src=True):
                src = script['src']
                if src.endswith('.js'):
                    full_url = urljoin(url, src)
                    js_files.append(full_url)
            
            print(f"📊 找到 {len(js_files)} 个JS文件:\n")
            for i, js_url in enumerate(js_files, 1):
                print(f"  {i}. {js_url}")
            
            return js_files
            
        except Exception as e:
            print(f"❌ 提取失败: {e}")
            return []
    
    def analyze_js_url(self, js_url):
        """分析远程JS文件"""
        print(f"\n{'='*80}")
        print(f"分析JS文件: {js_url}")
        print(f"{'='*80}\n")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(js_url, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                print(f"❌ 下载失败: HTTP {resp.status_code}")
                return None
            
            content = resp.text
            file_size = len(content)
            lines = content.splitlines()
            
            print(f"📊 文件大小: {file_size / 1024:.2f} KB")
            print(f"📄 总行数: {len(lines)}\n")
            
            # 逐行分析
            for pattern_name, patterns in self.patterns.items():
                for pattern in patterns:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            finding = {
                                'category': pattern_name,
                                'line': line_num,
                                'pattern': pattern,
                                'content': line.strip()[:200],
                                'source_file': js_url
                            }
                            self.findings.append(finding)
            
            # 显示结果
            if self.findings:
                print(f"\n🔍 发现 {len(self.findings)} 个潜在问题:\n")
                
                # 按类别分组
                categories = {}
                for f in self.findings:
                    cat = f['category']
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(f)
                
                for cat, findings in categories.items():
                    print(f"\n📌 {cat} ({len(findings)} 个):")
                    print('-' * 100)
                    for f in findings[:10]:
                        print(f"  行 {f['line']:<6} | {f['content'][:80]}")
                    if len(findings) > 10:
                        print(f"  ... 还有 {len(findings) - 10} 个")
            else:
                print("\n✅ 未发现明显的敏感信息或安全问题。")
            
            return content
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return None
            
    def save_report(self, filepath):
        """保存分析报告"""
        report = {
            'file': filepath,
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_findings': len(self.findings),
            'findings': self.findings
        }
        
        report_file = filepath + '.analysis.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n📝 详细报告已保存至: {report_file}")

def main():
    """主函数 - 从 first_target.txt 读取目标并分析"""
    print("JS 文件敏感信息扫描器")
    print("=" * 80)
    
    # 从 first_target.txt 读取目标URL
    target_file = os.path.join(os.path.dirname(__file__), 'urls', 'first_target.txt')
    
    if not os.path.exists(target_file):
        print(f"❌ 目标文件不存在: {target_file}")
        sys.exit(1)
    
    with open(target_file, 'r', encoding='utf-8') as f:
        base_url = f.read().strip()
    
    print(f"\n🎯 目标URL: {base_url}\n")
    
    analyzer = JSAnalyzer()
    
    # 步骤1: 从网页提取JS文件
    js_files = analyzer.extract_js_from_url(base_url)
    
    if not js_files:
        print("\n⚠️  未找到JS文件,尝试直接分析...")
        # 如果没有找到JS文件,尝试分析主页本身
        analyzer.analyze_js_url(base_url)
    else:
        # 步骤2: 分析每个JS文件(限制前10个)
        print(f"\n{'='*80}")
        print(f"开始分析 {min(len(js_files), 10)} 个JS文件...")
        print(f"{'='*80}")
        
        for i, js_url in enumerate(js_files[:10], 1):
            print(f"\n[{i}/{min(len(js_files), 10)}] 进度:")
            analyzer.analyze_js_url(js_url)
    
    # 步骤3: 保存总体报告
    if analyzer.findings:
        domain = urlparse(base_url).netloc
        output_dir = f"@{domain}_bounty"
        os.makedirs(output_dir, exist_ok=True)
        
        report_file = os.path.join(output_dir, 'js_secrets.json')
        report = {
            'target_url': base_url,
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_js_files': len(js_files),
            'total_findings': len(analyzer.findings),
            'findings': analyzer.findings
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"📝 详细报告已保存至: {report_file}")
        print(f"📊 共发现 {len(analyzer.findings)} 个潜在问题")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print("✅ 分析完成!未发现明显问题")
        print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
