#!/usr/bin/env python3
"""
Bing 搜索工具
使用 Bing 搜索引擎获取搜索结果

用法:
    python search.py "Python 教程"
    python search.py "Python 教程" --limit 10 --output results.json
"""

import re
import json
import urllib.request
import urllib.parse
import argparse
from html import unescape
from typing import List, Dict


def search_bing(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    使用 Bing 搜索

    Args:
        query: 搜索关键词
        limit: 返回结果数量

    Returns:
        搜索结果列表，每项包含 title、url、snippet
    """
    # 编码搜索词
    encoded_query = urllib.parse.quote(query)

    # 构造请求
    url = f"https://www.bing.com/search?q={encoded_query}&count={limit}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

    # 解析结果
    results = []

    # Bing 搜索结果的正则模式
    # 匹配搜索结果块
    result_pattern = r'<li class="b_algo"[^>]*>(.*?)</li>'
    result_blocks = re.findall(result_pattern, html, re.DOTALL)

    for block in result_blocks[:limit]:
        result = {}

        # 提取标题和链接
        title_pattern = r'<a[^>]*href="([^"]+)"[^>]*><h2>(.*?)</h2>'
        title_match = re.search(title_pattern, block, re.DOTALL)

        if title_match:
            result['url'] = unescape(title_match.group(1))
            # 清理标题中的 HTML 标签
            title = re.sub(r'<[^>]+>', '', title_match.group(2))
            result['title'] = unescape(title.strip())
        else:
            continue

        # 提取摘要
        snippet_pattern = r'<div class="b_caption"[^>]*>.*?p>(.*?)"</p>'
        snippet_match = re.search(snippet_pattern, block, re.DOTALL)

        if snippet_match:
            snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1))
            result['snippet'] = unescape(snippet.strip())
        else:
            # 尝试其他摘要模式
            alt_snippet_pattern = r'<span>(.*?)"</span>'
            alt_match = re.findall(alt_snippet_pattern, block)
            if alt_match:
                snippet = re.sub(r'<[^>]+>', '', alt_match[-1])
                result['snippet'] = unescape(snippet.strip())
            else:
                result['snippet'] = ''

        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(description='Bing 搜索工具')
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('--limit', '-l', type=int, default=10,
                        help='返回结果数量 (默认: 10)')
    parser.add_argument('--output', '-o', help='输出 JSON 文件')

    args = parser.parse_args()

    print(f"正在搜索: {args.query}")
    print("-" * 60)

    results = search_bing(args.query, args.limit)

    if not results:
        print("未找到搜索结果")
        return

    # 输出结果
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        if result.get('snippet'):
            snippet = result['snippet'][:150] + '...' if len(result['snippet']) > 150 else result['snippet']
            print(f"   摘要: {snippet}")

    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")


if __name__ == '__main__':
    main()
