#!/usr/bin/env python3
"""
记忆回忆脚本
搜索记忆文件获取相关上下文

用法:
    python recall.py "关键词" --limit 5
    python recall.py "数据库" --category tech --tags "架构"
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class MemoryRecall:
    """记忆回忆器"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)

    def recall(self, query: str, category: Optional[str] = None,
               tags: Optional[List[str]] = None, limit: int = 10) -> List[Dict]:
        """
        搜索记忆

        Args:
            query: 搜索关键词
            category: 分类过滤
            tags: 标签过滤
            limit: 返回数量限制

        Returns:
            匹配的记忆条目列表
        """
        results = []

        # 搜索所有记忆文件
        for memory_file in sorted(self.memory_dir.glob("*.md"), reverse=True):
            if memory_file.name == "index.md":
                continue

            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 按条目分割
            entries = self._parse_entries(content, memory_file.stem)

            for entry in entries:
                # 检查是否匹配
                if self._matches(entry, query, category, tags):
                    results.append(entry)

                    if len(results) >= limit:
                        return results

        return results

    def _parse_entries(self, content: str, date: str) -> List[Dict]:
        """解析记忆条目"""
        entries = []

        # 按 ## 分割
        pattern = r'##\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+\[([^\]]+)\]\n\n(.+?)(?=\n---|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)

        for date_str, time_str, category, body in matches:
            entry = {
                'date': date_str,
                'time': time_str,
                'category': category,
                'content': body.strip(),
                'raw': f"## {date_str} {time_str} [{category}]\n\n{body}"
            }

            # 提取标签
            tag_match = re.search(r'\*\*标签\*\*:\s*(.+)', body)
            if tag_match:
                entry['tags'] = [t.strip('#') for t in tag_match.group(1).split()]
            else:
                entry['tags'] = []

            entries.append(entry)

        return entries

    def _matches(self, entry: Dict, query: str, category: Optional[str],
                 tags: Optional[List[str]]) -> bool:
        """检查条目是否匹配查询条件"""
        # 检查关键词
        query_lower = query.lower()
        if query_lower not in entry['content'].lower() and \
           query_lower not in entry['category'].lower():
            return False

        # 检查分类
        if category and entry['category'].lower() != category.lower():
            return False

        # 检查标签
        if tags:
            entry_tags = set(t.lower() for t in entry['tags'])
            if not any(t.lower() in entry_tags for t in tags):
                return False

        return True


def main():
    parser = argparse.ArgumentParser(description='回忆记忆')
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('--category', '-c', help='分类过滤')
    parser.add_argument('--tags', '-t', help='标签过滤，逗号分隔')
    parser.add_argument('--limit', '-l', type=int, default=5,
                        help='返回数量限制')
    parser.add_argument('--memory-dir', '-d', default='memory',
                        help='记忆目录')

    args = parser.parse_args()

    tags = args.tags.split(',') if args.tags else []

    recall = MemoryRecall(args.memory_dir)
    results = recall.recall(args.query, args.category, tags, args.limit)

    if not results:
        print(f"未找到与 '{args.query}' 相关的记忆")
        return

    print(f"找到 {len(results)} 条相关记忆:\n")

    for i, entry in enumerate(results, 1):
        print(f"{i}. [{entry['date']} {entry['time']}] {entry['category']}")

        # 提取内容预览
        content_preview = entry['content'].split('\n')[0][:80]
        print(f"   {content_preview}...")

        if entry['tags']:
            print(f"   标签: {', '.join(entry['tags'])}")
        print()


if __name__ == '__main__':
    main()
