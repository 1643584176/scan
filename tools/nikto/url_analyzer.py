#!/usr/bin/env python3
"""
URL 分类和分析工具。
用法: python url_analyzer.py <all_urls.txt文件> [输出目录]
功能：
1. 读取 all_urls.txt
2. 按类型分类 URL (API、表单、静态资源等)
3. 提取参数和敏感点
4. 生成分类报告
5. 输出适合 SQLMap 测试的 URL 列表
"""

import os
import sys
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from collections import defaultdict

def log(message):
    """输出带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

class URLAnalyzer:
    def __init__(self):
        self.urls = []
        self.categories = {
            'api_endpoints': [],      # API 端点 (/api/*, /v1/*, *.json)
            'forms_with_params': [],  # 带参数的页面 (?id=1&user=admin)
            'login_auth': [],         # 登录/认证相关 (/login, /auth, /signin)
            'admin_panel': [],        # 管理后台 (/admin, /dashboard, /manage)
            'upload_files': [],       # 文件上传 (/upload, /attach)
            'search_pages': [],       # 搜索页面 (/search, /query)
            'static_resources': [],   # 静态资源 (.js, .css)
            'other_pages': []         # 其他页面
        }
        self.param_analysis = {}      # 参数统计分析
        self.sensitive_params = {}    # 敏感参数
        
    def load_urls(self, urls_file):
        """加载 URL 列表"""
        if not os.path.exists(urls_file):
            print(f"[ERROR] 文件不存在: {urls_file}")
            return False
        
        with open(urls_file, 'r', encoding='utf-8') as f:
            self.urls = [line.strip() for line in f if line.strip() and line.startswith('http')]
        
        log(f"加载 {len(self.urls)} 个 URL")
        return True
    
    def classify_url(self, url):
        """对单个 URL 进行分类（增强版）"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query
        filename = path.split('/')[-1].lower()
        
        # 1. API 端点检测（增强：支持更多模式）
        api_patterns = [
            '/api/', '/v1/', '/v2/', '/v3/', '/graphql', '/rest/',
            '/api-', '-api/', '/endpoint', '/webhook'
        ]
        if any(pattern in path for pattern in api_patterns):
            return 'api_endpoints'
        if filename.endswith(('.json', '.xml', '.yaml', '.yml')):
            return 'api_endpoints'
        # 检测 RESTful 风格：/users/123, /posts/456/comments
        import re
        if re.search(r'/\w+/\d+(/\w+)?$', path):
            return 'api_endpoints'
        
        # 2. 登录/认证相关（增强：支持 OAuth、SSO）
        auth_patterns = [
            '/login', '/auth', '/signin', '/signup', '/register', 
            '/logout', '/oauth', '/sso', '/session', '/token',
            '/authenticate', '/authorization', '/permission'
        ]
        if any(keyword in path for keyword in auth_patterns):
            return 'login_auth'
        
        # 3. 管理后台（增强：支持更多关键词）
        admin_patterns = [
            '/admin', '/dashboard', '/manage', '/control', '/panel', 
            '/backend', '/console', '/system', '/settings', '/config',
            '/moderator', '/supervisor', '/operator'
        ]
        if any(keyword in path for keyword in admin_patterns):
            return 'admin_panel'
        
        # 4. 文件上传（增强：支持导入/导出）
        upload_patterns = [
            '/upload', '/attach', '/import', '/export', '/download',
            '/file', '/document', '/media', '/asset'
        ]
        if any(keyword in path for keyword in upload_patterns):
            return 'upload_files'
        
        # 5. 搜索页面（增强：支持过滤/排序）
        search_patterns = [
            '/search', '/query', '/find', '/filter', '/sort',
            '/browse', '/explore', '/discover', '/lookup'
        ]
        if any(keyword in path for keyword in search_patterns):
            return 'search_pages'
        
        # 6. 带参数的页面（增强：区分敏感参数）
        if query:
            return 'forms_with_params'
        
        # 7. 静态资源（增强：支持更多类型）
        static_extensions = ('.js', '.css', '.map', '.ts', '.jsx', '.tsx')
        if filename.endswith(static_extensions):
            return 'static_resources'
        
        # 8. 其他
        return 'other_pages'
    
    def analyze_parameters(self, url):
        """分析 URL 中的参数"""
        parsed = urlparse(url)
        if not parsed.query:
            return None
        
        params = parse_qs(parsed.query)
        param_names = list(params.keys())
        
        # 敏感参数模式匹配
        sensitive_patterns = {
            'id': ['id', 'uid', 'pid', 'cid', 'oid', 'item_id', 'user_id'],
            'search': ['search', 'query', 'q', 'keyword', 'key', 'term'],
            'file': ['file', 'path', 'dir', 'folder', 'document', 'filename'],
            'url': ['url', 'link', 'redirect', 'return', 'next', 'dest', 'target'],
            'command': ['cmd', 'command', 'exec', 'execute', 'run', 'action'],
            'user': ['user', 'username', 'uname', 'login', 'email', 'account'],
            'inject': ['name', 'value', 'data', 'input', 'text', 'content', 'msg', 'message']
        }
        
        sensitive_found = []
        for param_name in param_names:
            param_lower = param_name.lower()
            for category, patterns in sensitive_patterns.items():
                if any(pattern == param_lower or pattern in param_lower for pattern in patterns):
                    sensitive_found.append({
                        'param': param_name,
                        'category': category,
                        'url': url
                    })
                    break
        
        return {
            'url': url,
            'params': param_names,
            'param_count': len(param_names),
            'sensitive': sensitive_found
        }
    
    def classify_all(self):
        """对所有 URL 进行分类"""
        log("开始分类分析...")
        
        for i, url in enumerate(self.urls, 1):
            category = self.classify_url(url)
            self.categories[category].append(url)
            
            # 分析参数
            if category == 'forms_with_params':
                param_info = self.analyze_parameters(url)
                if param_info:
                    self.param_analysis[url] = param_info
                    # 收集敏感参数
                    for sens in param_info['sensitive']:
                        cat = sens['category']
                        if cat not in self.sensitive_params:
                            self.sensitive_params[cat] = []
                        self.sensitive_params[cat].append(sens)
            
            if i % 50 == 0:
                print(f"   已处理 {i}/{len(self.urls)} 个 URL...", end='\r')
        
        log("分类完成!")
    
    def generate_report(self, output_dir):
        """生成分类报告"""
        # 使用固定文件名，每次覆盖
        
        # 1. 生成详细分类报告 (JSON)
        report_file = os.path.join(output_dir, 'url_classification.json')
        
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_urls': len(self.urls),
            'categories': {
                category: {
                    'count': len(urls),
                    'urls': urls[:20]  # 只保存前20个作为示例
                }
                for category, urls in self.categories.items()
            },
            'parameter_analysis': {
                'total_param_urls': len(self.param_analysis),
                'sensitive_params_summary': {
                    category: len(items)
                    for category, items in self.sensitive_params.items()
                }
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        log(f"分类报告: {report_file}")
        
        # 2. 生成 SQLMap 测试列表 (TXT)
        sqlmap_urls = []
        
        # 优先选择带敏感参数的 URL
        for category, items in self.sensitive_params.items():
            for item in items:
                if item['url'] not in sqlmap_urls:
                    sqlmap_urls.append(item['url'])
        
        # 补充其他带参数的 URL
        for url in self.categories['forms_with_params']:
            if url not in sqlmap_urls:
                sqlmap_urls.append(url)
        
        # 添加 API 端点 (可能有注入点)
        for url in self.categories['api_endpoints']:
            parsed = urlparse(url)
            if parsed.query and url not in sqlmap_urls:
                sqlmap_urls.append(url)
        
        sqlmap_file = os.path.join(output_dir, 'sqlmap_targets.txt')
        with open(sqlmap_file, 'w', encoding='utf-8') as f:
            for url in sqlmap_urls:
                f.write(url + '\n')
        
        log(f"SQLMap 测试列表: {sqlmap_file} ({len(sqlmap_urls)} 个 URL)")
        
        # 3. 生成 Markdown 摘要
        md_file = os.path.join(output_dir, 'url_analysis_summary.md')
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# URL 分类分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**总 URL 数**: {len(self.urls)}\n\n")
            
            f.write("## [INFO] 分类统计\n\n")
            f.write("| 分类 | 数量 | 说明 |\n")
            f.write("|------|------|------|\n")
            
            category_desc = {
                'api_endpoints': 'API 接口端点',
                'forms_with_params': '带参数的页面',
                'login_auth': '登录/认证页面',
                'admin_panel': '管理后台',
                'upload_files': '文件上传功能',
                'search_pages': '搜索/查询页面',
                'static_resources': '静态资源文件',
                'other_pages': '其他页面'
            }
            
            for category, urls in sorted(self.categories.items(), key=lambda x: len(x[1]), reverse=True):
                desc = category_desc.get(category, '')
                f.write(f"| {category} | {len(urls)} | {desc} |\n")
            
            f.write("\n## [INFO] 敏感参数分析\n\n")
            if self.sensitive_params:
                for category, items in sorted(self.sensitive_params.items(), key=lambda x: len(x[1]), reverse=True):
                    unique_urls = len(set(item['url'] for item in items))
                    f.write(f"### {category} ({unique_urls} 个 URL)\n\n")
                    for item in items[:5]:  # 显示前5个示例
                        f.write(f"- `{item['param']}` in [{item['url']}]({item['url']})\n")
                    f.write("\n")
            else:
                f.write("未发现明显的敏感参数\n\n")
            
            f.write("## [INFO] 建议\n\n")
            f.write("1. **高优先级**: 对 `forms_with_params` 和 `api_endpoints` 进行 SQL 注入测试\n")
            f.write("2. **中优先级**: 检查 `login_auth` 和 `admin_panel` 的认证绕过\n")
            f.write("3. **低优先级**: 验证 `upload_files` 的文件上传漏洞\n")
            f.write("4. **信息收集**: `static_resources` 可能泄露技术栈信息\n")
        
        log(f"分析摘要: {md_file}")
        
        return report_file, sqlmap_file, md_file
    
    def print_summary(self):
        """打印分类摘要"""
        log("\n" + "="*60)
        log("URL 分类统计")
        log("="*60)
        
        for category, urls in sorted(self.categories.items(), key=lambda x: len(x[1]), reverse=True):
            percentage = (len(urls) / len(self.urls) * 100) if self.urls else 0
            log(f"  {category:25s}: {len(urls):5d} ({percentage:5.1f}%)")
        
        log("="*60)
        
        if self.sensitive_params:
            log("敏感参数发现:")
            for category, items in sorted(self.sensitive_params.items(), key=lambda x: len(x[1]), reverse=True):
                unique_urls = len(set(item['url'] for item in items))
                log(f"  {category:20s}: {unique_urls} 个 URL")


def main():
    if len(sys.argv) < 2:
        print("用法: python url_analyzer.py <all_urls.txt文件> [输出目录]")
        print("\n示例:")
        print("  python url_analyzer.py @example.com_bounty/all_urls.txt @example.com_bounty")
        sys.exit(1)
    
    urls_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(urls_file)
    
    # 创建分析器
    analyzer = URLAnalyzer()
    
    # 加载 URL
    if not analyzer.load_urls(urls_file):
        sys.exit(1)
    
    # 分类
    analyzer.classify_all()
    
    # 打印摘要
    analyzer.print_summary()
    
    # 生成报告
    report_file, sqlmap_file, md_file = analyzer.generate_report(output_dir)
    
    log("分析完成!")
    log(f"   - 分类报告: {report_file}")
    log(f"   - SQLMap列表: {sqlmap_file}")
    log(f"   - 分析摘要: {md_file}")


if __name__ == "__main__":
    main()
