#!/usr/bin/env python3
"""
根据漏洞范围文档筛选可测试的URL
"""

import re

def filter_in_scope_urls():
    """筛选在漏洞范围内的URL"""
    
    # 读取所有URL
    with open('js/all_urls.txt', 'r', encoding='utf-8-sig', errors='ignore') as f:
        all_urls = [line.strip() for line in f if line.strip()]
    
    print(f"总URL数量: {len(all_urls)}")
    
    in_scope_urls = set()
    out_of_scope_count = 0
    
    for url in all_urls:
        # 1. 必须是 www.sembcorp.com 主站（排除子域名）
        if not url.startswith('https://www.sembcorp.com/'):
            out_of_scope_count += 1
            continue
        
        # 2. 排除 media.sembcorp.com（子域名）
        if 'media.sembcorp.com' in url:
            out_of_scope_count += 1
            continue
        
        # 3. 排除 webint.sembcorp.com（子域名）
        if 'webint.sembcorp.com' in url:
            out_of_scope_count += 1
            continue
        
        # 4. 排除第三方服务
        if any(domain in url for domain in [
            'linkedin.com',
            'google.com',
            'googletagmanager.com',
            'googleapis.com',
            'recaptcha.net',
            'cloudflare.com',
            'facebook.com',
            'twitter.com',
            'youtube.com'
        ]):
            out_of_scope_count += 1
            continue
        
        # 5. 排除交互式功能（Contact Us, Careers, Forms等）
        if any(path in url.lower() for path in [
            '/contact-us/',
            '/careers/',
            '/forms/',
            '/subscribe/',
            '/email-alerts/',
            '/all-sites/',
            '/sitemap/'
        ]):
            out_of_scope_count += 1
            continue
        
        # 6. 排除特定业务单元（Wilton International, SSC等）
        if any(path in url.lower() for path in [
            '/wilton-international/',
            '/ssc/',
            '/sembcorp-specialised-construction/'
        ]):
            out_of_scope_count += 1
            continue
        
        # 7. 排除纯资源文件（CSS, JS, 图片等）
        if any(url.lower().endswith(ext) for ext in [
            '.css',
            '.js',
            '.jfif',
            '.jpg',
            '.png',
            '.gif',
            '.svg',
            '.ico',
            '.woff',
            '.woff2',
            '.ttf'
        ]):
            out_of_scope_count += 1
            continue
        
        # 8. 排除无效的URL（包含JavaScript代码片段的）
        if any(pattern in url for pattern in [
            '.concat(',
            '%28',  # URL编码的 (
            '/js/...',
            "''",
            'undefined'
        ]):
            out_of_scope_count += 1
            continue
        
        # 9. 保留静态页面
        # - 首页
        # - /about-us/*
        # - /driving-energy-transition/*
        # - /news-and-insights/*
        # - /creating-shareholder-value/*
        # - /site-services-pages/* (隐私政策等)
        # - /sg/* (新加坡站点 - 静态页面)
        # - /uk/* (英国站点 - 静态页面)
        # - /in/* (印度站点 - 静态页面)
        # - /cn/* (中国站点 - 静态页面)
        # - /id/* (印尼站点 - 静态页面)
        # - /om/* (阿曼站点 - 静态页面)
        # - /ph/* (菲律宾站点 - 静态页面)
        # - /cookie-policy-and-preferences/*
        
        in_scope_urls.add(url)
    
    # 转换为列表并排序
    sorted_urls = sorted(in_scope_urls)
    
    print(f"在范围内的URL: {len(sorted_urls)}")
    print(f"排除的URL: {out_of_scope_count}")
    
    # 保存到文件
    output_file = 'js/in_scope_urls_filtered.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Sembcorp 可测试URL列表\n")
        f.write("# 根据漏洞范围文档筛选\n")
        f.write(f"# 生成时间: 2026-05-21\n")
        f.write(f"# 总数: {len(sorted_urls)}\n")
        f.write("\n")
        
        for url in sorted_urls:
            f.write(url + '\n')
    
    print(f"\n✅ 已保存到: {output_file}")
    
    # 统计各类URL数量
    stats = {
        '首页': 0,
        '关于我们': 0,
        '业务介绍': 0,
        '新闻和洞察': 0,
        '投资者关系': 0,
        '国家站点-SG': 0,
        '国家站点-UK': 0,
        '国家站点-IN': 0,
        '国家站点-CN': 0,
        '国家站点-ID': 0,
        '国家站点-其他': 0,
        'Cookie策略': 0,
        '其他': 0
    }
    
    for url in sorted_urls:
        if url == 'https://www.sembcorp.com/':
            stats['首页'] += 1
        elif '/about-us/' in url:
            stats['关于我们'] += 1
        elif '/driving-energy-transition/' in url:
            stats['业务介绍'] += 1
        elif '/news-and-insights/' in url:
            stats['新闻和洞察'] += 1
        elif '/creating-shareholder-value/' in url or '/investors/' in url:
            stats['投资者关系'] += 1
        elif '/sg/' in url:
            stats['国家站点-SG'] += 1
        elif '/uk/' in url:
            stats['国家站点-UK'] += 1
        elif '/in/' in url:
            stats['国家站点-IN'] += 1
        elif '/cn/' in url:
            stats['国家站点-CN'] += 1
        elif '/id/' in url:
            stats['国家站点-ID'] += 1
        elif any(f'/{country}/' in url for country in ['om', 'ph', 'th', 'vn']):
            stats['国家站点-其他'] += 1
        elif '/cookie-policy' in url:
            stats['Cookie策略'] += 1
        else:
            stats['其他'] += 1
    
    print("\n📊 URL分类统计:")
    print("=" * 50)
    for category, count in stats.items():
        if count > 0:
            print(f"  {category}: {count}")

if __name__ == '__main__':
    filter_in_scope_urls()
