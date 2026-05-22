#!/usr/bin/env python3
"""
对比各个国家站点的URL结构，检查接口是否一致
"""

from collections import defaultdict
import re

def analyze_country_sites():
    """分析各个国家站点的URL结构"""
    
    # 读取URL列表
    with open('js/in_scope_urls_filtered.txt', 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # 按国家站点分组
    country_urls = defaultdict(list)
    
    for url in urls:
        # 提取国家代码
        match = re.search(r'/([a-z]{2})/', url)
        if match:
            country_code = match.group(1)
            # 排除非国家代码（如 en, ar 等语言代码）
            if country_code not in ['en', 'ar', 'id']:  # id 是印尼，但 /id/en/ 需要特殊处理
                country_urls[country_code].append(url)
            elif country_code == 'id' and '/id/en/' in url:
                country_urls['id'].append(url)
            elif country_code == 'id' and '/id/id/' in url:
                country_urls['id'].append(url)
    
    print("=" * 80)
    print("各国家站点URL数量统计")
    print("=" * 80)
    
    for country in sorted(country_urls.keys()):
        count = len(country_urls[country])
        print(f"  {country}: {count} 个URL")
    
    print("\n" + "=" * 80)
    print("URL结构对比分析")
    print("=" * 80)
    
    # 提取每个国家站点的URL路径模式
    country_patterns = {}
    for country, urls in country_urls.items():
        patterns = set()
        for url in urls:
            # 移除域名部分，只保留路径
            path = url.replace('https://www.sembcorp.com', '')
            # 移除具体的文章ID或动态参数，保留路径结构
            # 例如: /news/article/123 -> /news/article/*
            normalized = re.sub(r'/[^/]+/\d+', '/*', path)
            patterns.add(normalized)
        
        country_patterns[country] = sorted(patterns)
    
    # 找出所有国家的共同模式
    all_countries = list(country_patterns.keys())
    if len(all_countries) >= 2:
        common_patterns = set(country_patterns[all_countries[0]])
        for country in all_countries[1:]:
            common_patterns &= set(country_patterns[country])
        
        print(f"\n✅ 共同URL模式 ({len(common_patterns)} 个):")
        for pattern in sorted(common_patterns)[:20]:  # 只显示前20个
            print(f"  {pattern}")
        if len(common_patterns) > 20:
            print(f"  ... 还有 {len(common_patterns) - 20} 个")
    
    # 找出每个国家特有的模式
    print("\n" + "=" * 80)
    print("各国特有URL模式")
    print("=" * 80)
    
    for country in sorted(country_patterns.keys()):
        other_patterns = set()
        for c in country_patterns:
            if c != country:
                other_patterns |= set(country_patterns[c])
        
        unique_patterns = set(country_patterns[country]) - other_patterns
        
        if unique_patterns:
            print(f"\n🔸 {country} 特有模式 ({len(unique_patterns)} 个):")
            for pattern in sorted(unique_patterns)[:10]:  # 只显示前10个
                print(f"  {pattern}")
            if len(unique_patterns) > 10:
                print(f"  ... 还有 {len(unique_patterns) - 10} 个")
        else:
            print(f"\n✓ {country}: 无特有模式（完全使用通用结构）")
    
    # 详细对比几个主要国家站点
    print("\n" + "=" * 80)
    print("主要国家站点详细对比")
    print("=" * 80)
    
    major_countries = ['sg', 'uk', 'in', 'cn', 'id']
    for country in major_countries:
        if country in country_patterns:
            print(f"\n📍 {country.upper()} 站点:")
            print(f"  URL总数: {len(country_urls[country])}")
            print(f"  路径模式数: {len(country_patterns[country])}")
            
            # 显示前10个典型URL
            print(f"  典型URL示例:")
            for url in country_urls[country][:5]:
                path = url.replace('https://www.sembcorp.com', '')
                print(f"    {path}")
    
    # 检查是否有API端点
    print("\n" + "=" * 80)
    print("API端点检查")
    print("=" * 80)
    
    api_endpoints = []
    for url in urls:
        if '/api/' in url.lower() or '/umbraco/' in url.lower():
            api_endpoints.append(url)
    
    if api_endpoints:
        print(f"\n发现 {len(api_endpoints)} 个API端点:")
        for endpoint in api_endpoints[:20]:
            print(f"  {endpoint}")
        if len(api_endpoints) > 20:
            print(f"  ... 还有 {len(api_endpoints) - 20} 个")
    else:
        print("\n✓ 未发现明显的API端点")
    
    # 保存详细报告
    report_file = 'js/country_sites_comparison.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Sembcorp 各国家站点URL结构对比报告\n\n")
        f.write(f"生成时间: 2026-05-21\n\n")
        
        f.write("## URL数量统计\n\n")
        for country in sorted(country_urls.keys()):
            f.write(f"- **{country}**: {len(country_urls[country])} 个URL\n")
        
        f.write("\n## 共同URL模式\n\n")
        f.write("以下模式在所有国家站点中都存在：\n\n```")
        for pattern in sorted(common_patterns):
            f.write(f"\n{pattern}")
        f.write("\n```\n")
        
        f.write("\n## 各国特有模式\n\n")
        for country in sorted(country_patterns.keys()):
            other_patterns = set()
            for c in country_patterns:
                if c != country:
                    other_patterns |= set(country_patterns[c])
            
            unique_patterns = set(country_patterns[country]) - other_patterns
            
            if unique_patterns:
                f.write(f"### {country.upper()}\n\n```")
                for pattern in sorted(unique_patterns):
                    f.write(f"\n{pattern}")
                f.write("\n```\n\n")
    
    print(f"\n✅ 详细报告已保存到: {report_file}")

if __name__ == '__main__':
    analyze_country_sites()
