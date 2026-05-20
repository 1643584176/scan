#!/usr/bin/env python3
"""
URL 收集和去重工具（使用 Katana + httpx）。
用法: python url_collector.py <目标URL> [输出目录]
功能：
1. 使用 Katana 爬取 URL
2. 使用 httpx 验证并去重
3. 保存到 all_urls.txt
4. 如果已存在 all_urls.txt，则跳过爬取，直接使用
"""

import sys
import os
import warnings
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    # 设置 Windows 控制台编码
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except:
        pass

warnings.filterwarnings('ignore')  # 抑制所有警告

import subprocess
import time
from datetime import datetime

def log(message):
    """输出带时间戳的日志（强制刷新）"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)  # 强制刷新输出

def check_all_urls_exists(output_dir):
    """检查是否已存在 all_urls.txt"""
    all_urls_file = os.path.join(output_dir, 'all_urls.txt')
    if os.path.exists(all_urls_file):
        with open(all_urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        log(f"[INFO] 发现已有的 all_urls.txt，包含 {len(urls)} 个 URL")
        return True, all_urls_file, urls
    return False, None, []

def clean_url(url):
    """清理 URL 格式"""
    if not url:
        return None
    
    # 移除空白字符
    url = url.strip()
    
    # 移除末尾的反斜杠和 URL 编码的反斜杠
    url = url.replace('%5C', '').replace('%5c', '').replace('\\', '')
    
    # 再次移除可能因删除反斜杠产生的末尾空白
    url = url.strip()
    
    # 必须是以 http 开头
    if not url.startswith('http://') and not url.startswith('https://'):
        return None
        
    return url

def run_katana_streaming(target, output_dir, target_domain=None):
    """使用 Katana 爬取 URL（临时文件轮询模式）"""
    log("[INFO] 启动 Katana 爬虫 (实时过滤模式)...")
    
    # 直接使用系统 PATH 中的 katana 命令
    katana_exe = 'katana'
    
    # 1. 先让 Katana 输出到一个临时文件
    temp_raw = os.path.join(output_dir, 'katana_temp_raw.txt')
    all_urls_file = os.path.join(output_dir, 'all_urls.txt')
    
    cmd = [
        katana_exe,
        '-u', target,
        '-d', '2',           
        '-silent',           
        '-c', '5',           
        '-timeout', '15',    
        '-mrs', '5120',      
        '-f', 'url',         
        '-known-files', 'all',
        '-js-crawl',         
        '-o', temp_raw       # 输出到临时文件
    ]
    
    seen_urls = set()
    valid_count = 0
    
    try:
        # 启动 Katana 后台运行
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, # 彻底屏蔽 stderr 避免 GBK 崩溃
            # 不使用 text=True，避免编码问题
        )
        
        log(f"   [WAIT] Katana 正在后台爬取，实时过滤中...")
        
        # 2. 实时轮询临时文件并进行过滤
        last_size = 0
        while process.poll() is None: # 只要进程还在跑
            if os.path.exists(temp_raw):
                with open(temp_raw, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # 处理新产生的行
                for line in lines[last_size:]:
                    url = clean_url(line)
                    if not url: continue
                    
                    # 实时过滤逻辑
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    path = parsed.path.lower()
                    domain = parsed.netloc.lower()
                    
                    # 域名校验
                    if target_domain:
                        main_domain = '.'.join(target_domain.lower().split('.')[-2:])
                        if not (domain == target_domain.lower() or domain.endswith('.' + main_domain)):
                            continue
                    
                    # 扩展名过滤
                    ext = ''
                    if '.' in path.split('/')[-1]:
                        ext = '.' + path.split('/')[-1].split('.')[-1]
                    exclude_exts = {'.css', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.woff', '.woff2', '.ttf'}
                    if ext in exclude_exts: continue
                    
                    # 路径过滤
                    skip_patterns = ['/_next/static/', '/_next/image', '/static/images/', '/fonts/']
                    if any(p in url.lower() for p in skip_patterns): continue
                    
                    # 去重并写入最终文件
                    if url not in seen_urls:
                        seen_urls.add(url)
                        with open(all_urls_file, 'a', encoding='utf-8') as f_out:
                            f_out.write(url + '\n')
                        valid_count += 1
                        if valid_count % 20 == 0:
                            log(f"   [INFO] 已实时过滤并保存 {valid_count} 个有效 URL...", end='\r')
                
                last_size = len(lines)
            time.sleep(0.5) # 每 0.5 秒检查一次
        
        # 进程结束后再最后检查一次
        if os.path.exists(temp_raw):
            with open(temp_raw, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            for line in lines[last_size:]:
                url = clean_url(line)
                if url and url not in seen_urls:
                    # 再次执行过滤逻辑（简化版）
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower()
                    if target_domain and not (domain == target_domain.lower() or domain.endswith('.' + '.'.join(target_domain.lower().split('.')[-2:]))):
                        continue
                    seen_urls.add(url)
                    with open(all_urls_file, 'a', encoding='utf-8') as f_out:
                        f_out.write(url + '\n')
                    valid_count += 1

        log(f"\n[OK] Katana 爬取完成: 共发现 {valid_count} 个高质量 URL")
        
        # 清理临时文件
        if os.path.exists(temp_raw): os.remove(temp_raw)
        
        return list(seen_urls)
        
    except Exception as e:
        log(f"[ERROR] Katana 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def run_katana(target, output_dir, cookies=None):
    """
    使用 Katana 爬取 URL
    
    Args:
        target: 目标 URL
        output_dir: 输出目录
        cookies: Cookie 字符串（可选），格式: "name1=value1; name2=value2"
    """
    log("[KATANA] 启动 Katana 爬虫...")
    log("[WAIT] 请稍候，Katana 正在初始化...")
    
    # 直接使用系统 PATH 中的 katana 命令
    katana_exe = 'katana'
    
    # 使用绝对路径，固定文件名（不带日期）
    output_file = os.path.abspath(os.path.join(output_dir, 'katana_raw.txt'))
    
    cmd = [
        katana_exe,
        '-u', target,
        '-d', '3',           # 深度 3（爬取首页 + 一级链接 + 二级链接）
        '-c', '10',          # 并发数 10（提高并发）
        '-timeout', '5',     # 每个请求超时 5 秒（快速失败）
        '-f', 'url',         # 只输出 URL
        '-known-files', 'all', # 爬取 robots.txt、sitemap.xml
        '-silent'             # 静默模式，减少输出
        # 注意：不使用 -mrs 限制，避免遗漏大型页面和 JS 文件
    ]
    
    # 如果提供了 Cookie，添加到命令中
    if cookies:
        cmd.extend(['-headers', f'Cookie: {cookies}'])
        log(f"[INFO] 使用提供的 Cookie 进行认证爬取")
    
    try:
        log(f"   [CMD] Katana 命令: {' '.join(cmd)}")
        log(f"   [WAIT] Katana 正在爬取，请稍候...")
        
        # 打开输出文件
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # 运行 Katana，输出到文件和控制台
            result = subprocess.run(
                cmd,
                stdout=outfile,  # 输出到文件
                stderr=subprocess.STDOUT,  # stderr 也输出到文件
                timeout=180  # 180秒总超时（3分钟，适应更深的爬取）
            )
        
        log(f"\n   [OK] Katana 爬取完成，返回码: {result.returncode}")
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            log(f"   [FILE] katana_raw.txt 大小: {file_size} bytes")
            
            # 读取原始 URL（过滤空行）
            with open(output_file, 'r', encoding='utf-8') as f:
                raw_urls = [line.strip() for line in f if line.strip()]
            
            log(f"   [INFO] Katana 爬取到 {len(raw_urls)} 个 URL")
            
            # 显示前10个 URL 作为示例
            if raw_urls:
                log(f"   [URLS] 示例 URL (前10个):")
                for i, url in enumerate(raw_urls[:10], 1):
                    log(f"      {i}. {url}")
                if len(raw_urls) > 10:
                    log(f"      ... 还有 {len(raw_urls) - 10} 个 URL")
            
            # 清理并去重
            cleaned_urls = set()
            for url in raw_urls:
                clean = clean_url(url)
                if clean:
                    cleaned_urls.add(clean)
            
            final_urls = sorted(list(cleaned_urls))
            
            # 写回清理后的结果（无空行）
            with open(output_file, 'w', encoding='utf-8') as f:
                for url in final_urls:
                    f.write(url + '\n')
            
            duplicates_removed = len(raw_urls) - len(final_urls)
            log(f"[OK] Katana 爬取完成: {len(final_urls)} 个唯一 URL (移除 {duplicates_removed} 个重复/无效)")
            return final_urls
        else:
            log("[WARN] Katana 未生成输出文件")
            return []
    except subprocess.TimeoutExpired:
        log(f"[ERROR] Katana 超时（60秒），尝试降级方案...")
        log(f"[INFO] 使用目标 URL 作为备用")
        
        # 降级方案：至少返回目标 URL 本身
        fallback_urls = [target]
        
        # 尝试爬取 robots.txt 和 sitemap.xml
        import requests
        try:
            # 爬取 robots.txt
            robots_url = target.rstrip('/') + '/robots.txt'
            resp = requests.get(robots_url, timeout=10)
            if resp.status_code == 200:
                log(f"[INFO] 发现 robots.txt，解析中...")
                for line in resp.text.splitlines():
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        log(f"[INFO] 发现 sitemap: {sitemap_url}")
                        # 解析 sitemap
                        try:
                            sitemap_resp = requests.get(sitemap_url, timeout=10)
                            if sitemap_resp.status_code == 200:
                                import re
                                urls_in_sitemap = re.findall(r'<loc>([^<]+)</loc>', sitemap_resp.text)
                                fallback_urls.extend(urls_in_sitemap)
                                log(f"[INFO] 从 sitemap 获取 {len(urls_in_sitemap)} 个 URL")
                        except:
                            pass
                    elif line.lower().startswith('allow:') or line.lower().startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path and path != '/' and not path.startswith('*'):
                            full_url = target.rstrip('/') + path
                            fallback_urls.append(full_url)
        except Exception as e:
            log(f"[WARN] 无法爬取 robots.txt: {e}")
        
        # 保存备用 URL
        fallback_urls = list(set(fallback_urls))  # 去重
        if fallback_urls:
            with open(output_file, 'w', encoding='utf-8') as f:
                for url in fallback_urls:
                    f.write(url + '\n')
            log(f"[OK] 备用方案: 保存 {len(fallback_urls)} 个 URL")
            return fallback_urls
        else:
            log("[ERROR] 备用方案也失败，返回空列表")
            return []
    except Exception as e:
        log(f"[ERROR] Katana 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def run_httpx(urls, output_dir):
    """使用 httpx 验证 URL 有效性"""
    log(f"[HTTPX] 使用 httpx 验证 {len(urls)} 个 URL...")
    
    # 先写入临时文件
    temp_input = os.path.join(output_dir, 'temp_urls.txt')
    with open(temp_input, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')
    
    # 使用 Go 安装的 httpx（ProjectDiscovery 版本）
    # 避免与 Python 的 httpx 库冲突
    import shutil
    httpx_exe = shutil.which('httpx-toolkit') or shutil.which('httpx') or 'httpx'
    
    # 如果找到的是 Python 的 httpx，尝试直接使用 Go bin 路径
    if 'python' in httpx_exe.lower() or 'scripts' in httpx_exe.lower():
        # 尝试常见的 Go bin 路径
        go_bin_paths = [
            os.path.expanduser('~\\go\\bin\\httpx.exe'),
            os.path.expanduser('~\\.local\\bin\\httpx'),
            '/usr/local/bin/httpx',
        ]
        for path in go_bin_paths:
            if os.path.exists(path):
                httpx_exe = path
                break
    
    # 固定文件名（不带日期）
    output_file = os.path.join(output_dir, 'httpx_valid.txt')
    
    cmd = [
        httpx_exe,
        '-l', temp_input,
        '-o', output_file,
        '-mc', '200,201,204,301,302,307,403',  # 只保留这些状态码
        '-silent',
        '-timeout', '8',     # 单个请求超时 8 秒（生产接口合理值）
        '-retries', '0',     # 不重试，加快速度
        '-t', '50'           # 使用 50 个线程，加快速度
    ]
    
    try:
        log(f"   [CMD] httpx 命令: {' '.join(cmd)}")
        log(f"   [WAIT] httpx 正在验证 {len(urls)} 个 URL...")
        
        # 不使用 capture_output，直接显示输出，避免缓冲区阻塞
        result = subprocess.run(cmd, timeout=300)  # 5分钟总超时
        
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                valid_urls = [line.strip() for line in f if line.strip()]
            
            log(f"   [OK] httpx 验证完成，{len(valid_urls)} 个有效 URL")
            
            # 清理临时文件
            if os.path.exists(temp_input):
                os.remove(temp_input)
            
            return valid_urls
        else:
            log("   [WARN] httpx 未生成输出文件")
            return []
    except subprocess.TimeoutExpired:
        log(f"[ERROR] httpx 验证超时（300秒）")
        log(f"[INFO] 直接使用原始 URL 继续扫描")
        
        # 降级方案：直接返回原始 URL，不进行验证
        if os.path.exists(temp_input):
            os.remove(temp_input)
        return urls  # 返回所有原始 URL
    except Exception as e:
        log(f"[ERROR] httpx 验证失败: {e}")
        log(f"[INFO] 直接使用原始 URL 继续扫描")
        
        # 降级方案：直接返回原始 URL，不进行验证
        if os.path.exists(temp_input):
            os.remove(temp_input)
        return urls  # 返回所有原始 URL

def filter_urls(urls, target_domain=None):
    """过滤掉不需要扫描的 URL"""
    filtered = []
    
    # 需要排除的文件扩展名
    exclude_extensions = {
        '.css', '.scss', '.less',  # 样式表
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.bmp',  # 图片
        '.woff', '.woff2', '.ttf', '.eot', '.otf',  # 字体
        '.mp4', '.webm', '.avi', '.mov',  # 视频
        '.mp3', '.wav', '.ogg',  # 音频
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',  # 文档
        '.zip', '.rar', '.tar', '.gz',  # 压缩包
    }
    
    # 需要排除的路径模式
    exclude_patterns = [
        '/_next/static/',  # Next.js 静态资源
        '/_next/image',  # Next.js 图片服务
        '/assets/images/',  # 常见图片目录
        '/static/images/',
        '/img/',
        '/images/',
        '/fonts/',  # 字体目录
        '/font/',   # 单数字体目录
        '/vendor/',  # 第三方库
        '/node_modules/',
        '/chunks/',  # Next.js 构建产物
        '/dist/',  # 构建产物
        '/build/',  # 构建产物
    ]
    
    for url in urls:
        # 清理 URL：移除末尾的反斜杠和空白字符
        url = url.strip().rstrip('\\').rstrip('/')
        if not url:
            continue
        
        # 修复 URL 编码问题：移除 %5C (反斜杠)
        url = url.replace('%5C', '').replace('%5c', '')
        
        url_lower = url.lower()
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.lower()
        domain = parsed.netloc.lower()
        
        # 【关键】域名过滤：只保留目标域名及其子域名
        if target_domain:
            # 提取目标域名的主域名部分（例如：www.anthropic.com -> anthropic.com）
            target_parts = target_domain.lower().split('.')
            if len(target_parts) >= 2:
                main_domain = '.'.join(target_parts[-2:])  # 最后两部分，如 anthropic.com
            else:
                main_domain = target_domain.lower()
            
            # 检查 URL 的域名是否属于目标域名
            # 允许：完全匹配、子域名、主域名本身
            if not (domain == target_domain.lower() or 
                    domain == main_domain or  # 允许主域名本身（如 anthropic.com）
                    domain.endswith('.' + main_domain)):
                continue  # 跳过非目标域名的 URL
        
        # 获取文件扩展名
        ext = ''
        if '.' in path.split('/')[-1]:
            ext = '.' + path.split('/')[-1].split('.')[-1]
        
        # 如果是不需要的扩展名，跳过
        # 特殊处理：保留可能包含 API 端点的 JS 文件
        if ext in exclude_extensions and ext != '.js':
            continue
        
        # 检查路径模式
        skip = False
        for pattern in exclude_patterns:
            if pattern in url_lower:
                skip = True
                break
        
        if skip:
            continue
        
        filtered.append(url)
    
    return filtered

def merge_and_save_urls(new_urls, existing_urls, output_dir, target_domain=None):
    """合并新旧 URL，去重排序后保存"""
    # 合并
    all_urls = set(existing_urls) | set(new_urls)
    
    # 过滤掉不需要的 URL
    log(f"[INFO] 过滤前: {len(all_urls)} 个 URL")
    cleaned_urls = filter_urls(list(all_urls), target_domain)
    log(f"[OK] 过滤后: {len(cleaned_urls)} 个 URL (移除 {len(all_urls) - len(cleaned_urls)} 个无效资源)")
    
    # 标准化
    final_urls = []
    for url in cleaned_urls:
        url = url.strip()
        if url and (url.startswith('http://') or url.startswith('https://')):
            final_urls.append(url)
    
    # 排序
    final_urls.sort()
    
    # 保存
    all_urls_file = os.path.join(output_dir, 'all_urls.txt')
    with open(all_urls_file, 'w', encoding='utf-8') as f:
        for url in final_urls:
            f.write(url + '\n')
    
    log(f"[SAVE] 已保存 {len(final_urls)} 个 URL 到 all_urls.txt")
    
    # 显示新增数量
    new_count = len(final_urls) - len(existing_urls)
    if new_count > 0:
        log(f"[NEW] 新增 {new_count} 个 URL")
    else:
        log(f"[INFO] 无新增 URL")
    
    return final_urls

def collect_urls(target, output_dir='.'):
    """主函数"""
    log(f"\n[TARGET] 目标: {target}")
    log(f"[DIR] 目录: {output_dir}\n")
    
    # 提取目标域名（用于过滤）
    from urllib.parse import urlparse
    parsed = urlparse(target)
    target_domain = parsed.netloc  # 例如：www.anthropic.com
    log(f"[DOMAIN] 目标域名: {target_domain}")
    
    # 检查是否已有 all_urls.txt
    exists, all_urls_file, existing_urls = check_all_urls_exists(output_dir)
    
    if exists:
        log("[INFO] 使用现有的 all_urls.txt，跳过爬取阶段\n")
        return existing_urls
    
    # 删除旧的 katana_raw.txt 和 httpx_valid.txt（如果存在）
    old_katana = os.path.join(output_dir, 'katana_raw.txt')
    old_httpx = os.path.join(output_dir, 'httpx_valid.txt')
    if os.path.exists(old_katana):
        try:
            os.remove(old_katana)
            log("[DEL] 已删除旧的 katana_raw.txt")
        except PermissionError:
            log("[WARN] katana_raw.txt 被占用，跳过删除")
    if os.path.exists(old_httpx):
        try:
            os.remove(old_httpx)
            log("[DEL] 已删除旧的 httpx_valid.txt")
        except PermissionError:
            log("[WARN] httpx_valid.txt 被占用，跳过删除")
    
    # 第一步：Katana 爬取（使用简单模式，更稳定）
    # 尝试从环境变量读取 Cookie
    cookies = os.environ.get('KATANA_COOKIES', None)
    if cookies:
        log(f"[INFO] 检测到 KATANA_COOKIES 环境变量，将用于认证爬取")
    
    raw_urls = run_katana(target, output_dir, cookies=cookies)
    
    if not raw_urls:
        log("[ERROR] 未发现任何 URL")
        return []
    
    # 第二步：过滤 URL（按域名、扩展名等）
    log(f"[FILTER] 过滤 URL...")
    filtered_urls = filter_urls(raw_urls, target_domain)
    log(f"[OK] 过滤后: {len(filtered_urls)} 个 URL (移除 {len(raw_urls) - len(filtered_urls)} 个无效资源)")
    
    # 第三步：httpx 验证
    valid_urls = run_httpx(filtered_urls, output_dir)
    
    if not valid_urls:
        log("[ERROR] 没有有效的 URL")
        return []
    
    # 第四步：合并保存
    final_urls = merge_and_save_urls(valid_urls, existing_urls, output_dir, target_domain)
    
    return final_urls

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python url_collector.py <目标URL> [输出目录]")
        print("\n示例:")
        print("  python url_collector.py http://example.com ./bounty_dir")
        sys.exit(1)
    
    target = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    collect_urls(target, output_dir)
