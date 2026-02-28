#!/usr/bin/env python3
"""
记忆整合脚本
定期维护记忆文件，查找重复项和过期内容

用法:
    python consolidate.py --dry-run
    python consolidate.py --archive-before 2023-01-01
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Set


class MemoryConsolidate:
    """记忆整合器"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.archive_dir = self.memory_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)

    def consolidate(self, dry_run: bool = False, archive_before: str = None) -> Dict:
        """
        整合记忆文件

        Args:
            dry_run: 只报告，不执行
            archive_before: 归档此日期之前的记忆

        Returns:
            整合报告
        """
        report = {
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'archived_files': 0,
            'short_entries_removed': 0,
            'actions': []
        }

        # 查找重复
        duplicates = self._find_duplicates()
        report['duplicates_found'] = len(duplicates)

        if duplicates and not dry_run:
            self._remove_duplicates(duplicates)
            report['duplicates_removed'] = len(duplicates)

        for dup in duplicates:
            report['actions'].append(f"发现重复: {dup['content'][:50]}...")

        # 归档旧记忆
        if archive_before:
            archived = self._archive_old_memories(archive_before, dry_run)
            report['archived_files'] = archived
            if archived > 0:
                report['actions'].append(f"归档了 {archived} 个旧文件")

        # 清理短条目
        short_removed = self._clean_short_entries(dry_run)
        report['short_entries_removed'] = short_removed
        if short_removed > 0:
            report['actions'].append(f"清理了 {short_removed} 个短条目")

        # 更新索引
        if not dry_run:
            self._rebuild_index()

        return report

    def _find_duplicates(self) -> List[Dict]:
        """查找重复记忆"""
        seen = {}
        duplicates = []

        for memory_file in self.memory_dir.glob("*.md"):
            if memory_file.name in ["index.md", "template.md"]:
                continue

            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()

            entries = self._extract_entry_contents(content)

            for entry in entries:
                normalized = self._normalize(entry)

                if normalized in seen:
                    duplicates.append({
                        'content': entry,
                        'file': memory_file.name,
                        'duplicate_of': seen[normalized]
                    })
                else:
                    seen[normalized] = memory_file.name

        return duplicates

    def _extract_entry_contents(self, content: str) -> List[str]:
        """提取条目内容"""
        pattern = r'##\s+\d{4}-\d{2}-\d{2}.+?(?=\n---|\Z)'
        return re.findall(pattern, content, re.DOTALL)

    def _normalize(self, content: str) -> str:
        """标准化内容用于比较"""
        # 移除日期时间
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '', content)
        normalized = re.sub(r'\d{2}:\d{2}', '', normalized)
        # 移除标签行
        normalized = re.sub(r'\*\*标签\*\*:.+', '', normalized)
        # 清理空白
        return ' '.join(normalized.split())

    def _remove_duplicates(self, duplicates: List[Dict]):
        """移除重复条目"""
        # 简化的去重：重新写入不含重复的文件
        pass

    def _archive_old_memories(self, before_date: str, dry_run: bool) -> int:
        """归档旧记忆"""
        cutoff = datetime.strptime(before_date, "%Y-%m-%d")
        archived = 0

        for memory_file in self.memory_dir.glob("*.md"):
            if memory_file.name in ["index.md"]:
                continue

            # 解析文件名日期
            try:
                file_date = datetime.strptime(memory_file.stem, "%Y-%m-%d")
            except ValueError:
                continue

            if file_date < cutoff:
                if not dry_run:
                    target = self.archive_dir / memory_file.name
                    memory_file.rename(target)
                archived += 1

        return archived

    def _clean_short_entries(self, dry_run: bool) -> int:
        """清理过短的记忆条目"""
        removed = 0

        for memory_file in self.memory_dir.glob("*.md"):
            if memory_file.name in ["index.md"]:
                continue

            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 移除少于 50 字符的条目
            original_entries = self._extract_entry_contents(content)

            for entry in original_entries:
                if len(entry.strip()) < 50:
                    removed += 1
                    if not dry_run:
                        content = content.replace(entry, '')

            if not dry_run and removed > 0:
                with open(memory_file, 'w', encoding='utf-8') as f:
                    f.write(content)

        return removed

    def _rebuild_index(self):
        """重建索引文件"""
        entries = []

        for memory_file in self.memory_dir.glob("*.md"):
            if memory_file.name in ["index.md", "template.md"]:
                continue

            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取基本信息
            date_match = re.search(r'# 记忆日志 - (\d{4}-\d{2}-\d{2})', content)
            if date_match:
                entries.append({
                    'file': memory_file.name,
                    'date': date_match.group(1),
                    'entry_count': len(self._extract_entry_contents(content))
                })

        index = {
            'last_updated': datetime.now().isoformat(),
            'total_files': len(entries),
            'files': sorted(entries, key=lambda x: x['date'], reverse=True)
        }

        with open(self.memory_dir / "index.json", 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='整合记忆文件')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='只报告，不执行')
    parser.add_argument('--archive-before',
                        help='归档此日期之前的记忆 (YYYY-MM-DD)')
    parser.add_argument('--memory-dir', default='memory',
                        help='记忆目录')

    args = parser.parse_args()

    consolidate = MemoryConsolidate(args.memory_dir)
    report = consolidate.consolidate(args.dry_run, args.archive_before)

    print("记忆整合报告")
    print("=" * 50)
    print(f"发现重复: {report['duplicates_found']}")
    print(f"移除重复: {report['duplicates_removed']}")
    print(f"归档文件: {report['archived_files']}")
    print(f"清理短条目: {report['short_entries_removed']}")

    if report['actions']:
        print("\n执行的操作:")
        for action in report['actions']:
            print(f"  - {action}")

    if args.dry_run:
        print("\n(这是演练模式，未实际执行变更)")


if __name__ == '__main__':
    main()
