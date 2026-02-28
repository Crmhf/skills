#!/usr/bin/env python3
"""
记忆捕获脚本
从对话中提取关键事实并存储到每日日志

用法:
    python capture.py "关键信息" --category tech --tags "python,async"
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class MemoryCapture:
    """记忆捕获器"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)

    def capture(self, content: str, category: str = "general",
                tags: Optional[List[str]] = None, source: str = "") -> str:
        """
        捕获一条记忆

        Args:
            content: 记忆内容
            category: 分类 (tech/decision/meeting/idea)
            tags: 标签列表
            source: 来源/上下文

        Returns:
            记忆文件路径
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        # 构建记忆条目
        memory_entry = f"""
## {date_str} {time_str} [{category.upper()}]

**内容**: {content}

"""
        if source:
            memory_entry += f"**来源**: {source}\n\n"

        if tags:
            tag_str = " ".join(f"#{tag}" for tag in tags)
            memory_entry += f"**标签**: {tag_str}\n\n"

        memory_entry += "---\n"

        # 写入文件
        memory_file = self.memory_dir / f"{date_str}.md"

        if memory_file.exists():
            with open(memory_file, 'a', encoding='utf-8') as f:
                f.write(memory_entry)
        else:
            with open(memory_file, 'w', encoding='utf-8') as f:
                f.write(f"# 记忆日志 - {date_str}\n\n")
                f.write(memory_entry)

        # 更新索引
        self._update_index(date_str, content, category, tags)

        return str(memory_file)

    def _update_index(self, date: str, content: str, category: str,
                      tags: Optional[List[str]]):
        """更新索引文件"""
        index_file = self.memory_dir / "index.json"

        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"entries": []}

        index["entries"].append({
            "date": date,
            "category": category,
            "preview": content[:100] + "..." if len(content) > 100 else content,
            "tags": tags or []
        })

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='捕获记忆')
    parser.add_argument('content', help='记忆内容')
    parser.add_argument('--category', '-c', default='general',
                        choices=['general', 'tech', 'decision', 'meeting', 'idea'],
                        help='记忆分类')
    parser.add_argument('--tags', '-t', help='标签，逗号分隔')
    parser.add_argument('--source', '-s', help='来源/上下文')
    parser.add_argument('--memory-dir', '-d', default='memory',
                        help='记忆目录')

    args = parser.parse_args()

    tags = args.tags.split(',') if args.tags else []

    capture = MemoryCapture(args.memory_dir)
    file_path = capture.capture(args.content, args.category, tags, args.source)

    print(f"✓ 记忆已保存到: {file_path}")


if __name__ == '__main__':
    main()
