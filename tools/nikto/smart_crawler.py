#!/usr/bin/env python3
"""
智能爬虫和敏感参数发现工具。
用法: python smart_crawler.py <目标URL>
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import json
import sys
import warnings
from datetime import datetime

# 抑制 SSL 警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class SmartCrawler:
    def __init__(self, target_url):
        self.target_url = target_url.rstrip('/')
        self.domain = urlparse(target_url).netloc
        self.visited_urls = set()
        self.found_urls = []
        self.found_params = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def crawl(self, max_pages=30):
        """爬取网站，收集 URL 和参数"""
        # 不输出开始信息（由主程序控制）
        queue = [self.target_url]
        page_count = 0
        
        while queue and page_count < max_pages:
            url = queue.pop(0)
            
            if url in self.visited_urls:
                continue
            
            # 只爬取同域名
            if urlparse(url).netloc != self.domain:
                continue
                
            self.visited_urls.add(url)
            page_count += 1
            
            try:
                response = self.session.get(url, timeout=10, verify=False)
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取所有链接
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href'])
                    full_url = full_url.split('#')[0]  # 移除锚点
                    
                    if full_url not in self.visited_urls and urlparse(full_url).netloc == self.domain:
                        queue.append(full_url)
                        self.found_urls.append(full_url)
                        
                        # 提取参数
                        parsed = urlparse(full_url)
                        if parsed.query:
                            params = parse_qs(parsed.query)
                            for param_name in params.keys():
                                if param_name not in self.found_params:
                                    self.found_params[param_name] = []
                                self.found_params[param_name].append(full_url)
                
                # 提取表单
                for form in soup.find_all('form'):
                    action = form.get('action', '')
                    method = form.get('method', 'get').lower()
                    form_url = urljoin(url, action)
                    
                    for input_tag in form.find_all('input', {'name': True}):
                        param_name = input_tag['name']
                        if param_name not in self.found_params:
                            self.found_params[param_name] = []
                        self.found_params[param_name].append(f"{form_url} [{method}]")
                
                # 不再输出中间进度（由主程序控制）
                # if page_count % 10 == 0:
                #     print(f"  已爬取 {page_count} 页面, 发现 {len(self.found_urls)} URL, {len(self.found_params)} 参数")
                    
            except Exception as e:
                continue
        
        # 不输出完成信息（由主程序控制）
        return self.found_urls, self.found_params
    
    def find_sensitive_params(self):
        """识别敏感参数（可能的注入点）"""
        sensitive_patterns = {
            'id': ['id', 'uid', 'pid', 'cid', 'oid'],
            'search': ['search', 'query', 'q', 'keyword', 'key'],
            'file': ['file', 'path', 'dir', 'folder', 'document'],
            'url': ['url', 'link', 'redirect', 'return', 'next'],
            'command': ['cmd', 'command', 'exec', 'execute', 'run'],
            'user': ['user', 'username', 'uname', 'login', 'email'],
            'inject': ['name', 'value', 'data', 'input', 'text', 'content']
        }
        
        sensitive_found = {}
        for category, patterns in sensitive_patterns.items():
            for param_name in self.found_params.keys():
                param_lower = param_name.lower()
                if any(pattern in param_lower for pattern in patterns):
                    if category not in sensitive_found:
                        sensitive_found[category] = []
                    sensitive_found[category].extend(self.found_params[param_name])
        
        return sensitive_found
    
    def save_results(self, output_dir):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存所有 URL
        urls_file = f"{output_dir}/crawler_urls_{timestamp}.json"
        with open(urls_file, 'w', encoding='utf-8') as f:
            json.dump(list(set(self.found_urls)), f, indent=2, ensure_ascii=False)
        
        # 保存参数
        params_file = f"{output_dir}/crawler_params_{timestamp}.json"
        with open(params_file, 'w', encoding='utf-8') as f:
            json.dump(self.found_params, f, indent=2, ensure_ascii=False)
        
        # 保存敏感参数
        sensitive_file = f"{output_dir}/crawler_sensitive_{timestamp}.json"
        sensitive = self.find_sensitive_params()
        with open(sensitive_file, 'w', encoding='utf-8') as f:
            json.dump(sensitive, f, indent=2, ensure_ascii=False)
        
        # 不输出保存信息（由主程序控制）
        return urls_file, params_file, sensitive_file

def run_crawler(target, output_dir='.'):
    crawler = SmartCrawler(target)
    urls, params = crawler.crawl(max_pages=100)
    
    if urls or params:
        crawler.save_results(output_dir)
        
        # 显示敏感参数摘要
        sensitive = crawler.find_sensitive_params()
        if sensitive:
            print(f"\n⚠️  发现敏感参数类别:")
            for category, examples in sensitive.items():
                print(f"   {category}: {len(set(examples))} 个位置")
    
    return len(urls), len(params)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python smart_crawler.py <目标URL> [输出目录]")
        sys.exit(1)
    
    target = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    run_crawler(target, output_dir)
