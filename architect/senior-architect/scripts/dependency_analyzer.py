#!/usr/bin/env python3
"""
依赖分析器
分析项目依赖关系，检测循环依赖和模块耦合度

用法:
    python dependency_analyzer.py --path ./src
    python dependency_analyzer.py --path ./src --format json --output deps.json
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class DependencyInfo:
    """依赖信息"""
    module: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    coupling: float = 0.0  # 耦合度 (0-1)


@dataclass
class AnalysisResult:
    """分析结果"""
    modules: Dict[str, DependencyInfo] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)
    avg_coupling: float = 0.0
    high_coupling_modules: List[str] = field(default_factory=list)


class DependencyAnalyzer:
    """依赖分析器"""

    def __init__(self, project_path: str, threshold: float = 0.3):
        self.project_path = Path(project_path)
        self.threshold = threshold
        self.result = AnalysisResult()

    def analyze(self) -> AnalysisResult:
        """执行分析"""
        self._extract_dependencies()
        self._calculate_coupling()
        self._detect_cycles()
        self._identify_high_coupling()
        return self.result

    def _extract_dependencies(self):
        """提取模块依赖关系"""
        # 检测项目类型并提取依赖
        if self._is_java_project():
            self._extract_java_dependencies()
        elif self._is_python_project():
            self._extract_python_dependencies()
        elif self._is_js_project():
            self._extract_js_dependencies()
        else:
            self._extract_generic_dependencies()

    def _is_java_project(self) -> bool:
        return any(self.project_path.glob('pom.xml')) or \
               any(self.project_path.glob('build.gradle'))

    def _is_python_project(self) -> bool:
        return any(self.project_path.glob('requirements.txt')) or \
               any(self.project_path.glob('pyproject.toml'))

    def _is_js_project(self) -> bool:
        return any(self.project_path.glob('package.json'))

    def _extract_java_dependencies(self):
        """提取 Java 项目依赖"""
        src_path = self.project_path / 'src' / 'main' / 'java'
        if not src_path.exists():
            src_path = self.project_path

        package_map = {}

        # 第一轮：建立包名映射
        for java_file in src_path.rglob('*.java'):
            content = java_file.read_text(encoding='utf-8', errors='ignore')
            package_match = re.search(r'package\s+([\w.]+);', content)
            class_match = re.search(r'(?:class|interface)\s+(\w+)', content)

            if package_match and class_match:
                full_class = f"{package_match.group(1)}.{class_match.group(1)}"
                module_name = class_match.group(1)
                package_map[full_class] = module_name

                if module_name not in self.result.modules:
                    self.result.modules[module_name] = DependencyInfo(module=module_name)

        # 第二轮：提取 import 依赖
        for java_file in src_path.rglob('*.java'):
            content = java_file.read_text(encoding='utf-8', errors='ignore')
            class_match = re.search(r'(?:class|interface)\s+(\w+)', content)

            if class_match:
                module_name = class_match.group(1)
                imports = re.findall(r'import\s+([\w.]+);', content)

                for imp in imports:
                    for full_class, dep_module in package_map.items():
                        if imp in full_class and dep_module != module_name:
                            self.result.modules[module_name].dependencies.add(dep_module)
                            self.result.modules[dep_module].dependents.add(module_name)

    def _extract_python_dependencies(self):
        """提取 Python 项目依赖"""
        internal_modules = set()

        # 收集内部模块
        for py_file in self.project_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            module_name = py_file.stem
            internal_modules.add(module_name)

            if module_name not in self.result.modules:
                self.result.modules[module_name] = DependencyInfo(module=module_name)

        # 提取 import
        for py_file in self.project_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            content = py_file.read_text(encoding='utf-8', errors='ignore')
            module_name = py_file.stem

            # from X import Y 或 import X
            imports = re.findall(r'(?:from|import)\s+([\w.]+)', content)

            for imp in imports:
                base_module = imp.split('.')[0]
                if base_module in internal_modules and base_module != module_name:
                    self.result.modules[module_name].dependencies.add(base_module)
                    self.result.modules[base_module].dependents.add(module_name)

    def _extract_js_dependencies(self):
        """提取 JavaScript 项目依赖"""
        internal_modules = set()

        # 收集内部模块
        for ext in ['*.js', '*.ts']:
            for js_file in self.project_path.rglob(ext):
                if 'node_modules' in str(js_file):
                    continue
                module_name = js_file.stem
                internal_modules.add(module_name)

                if module_name not in self.result.modules:
                    self.result.modules[module_name] = DependencyInfo(module=module_name)

        # 提取 import
        for ext in ['*.js', '*.ts']:
            for js_file in self.project_path.rglob(ext):
                if 'node_modules' in str(js_file):
                    continue

                content = js_file.read_text(encoding='utf-8', errors='ignore')
                module_name = js_file.stem

                # import X from './path' 或 require('./path')
                imports = re.findall(r'(?:import|require)\s*\(?[\'"]([^\'"]+)', content)

                for imp in imports:
                    # 提取文件名
                    if './' in imp or '../' in imp:
                        base_name = Path(imp).stem
                        if base_name in internal_modules and base_name != module_name:
                            self.result.modules[module_name].dependencies.add(base_name)
                            self.result.modules[base_name].dependents.add(module_name)

    def _extract_generic_dependencies(self):
        """通用依赖提取"""
        # 按目录结构识别模块
        for item in self.project_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                module_name = item.name
                self.result.modules[module_name] = DependencyInfo(module=module_name)

                # 检查子目录引用
                for sub_item in item.rglob('*'):
                    if sub_item.is_file():
                        content = sub_item.read_text(encoding='utf-8', errors='ignore')
                        for other in self.result.modules:
                            if other != module_name and other in content:
                                self.result.modules[module_name].dependencies.add(other)

    def _calculate_coupling(self):
        """计算模块耦合度"""
        total_modules = len(self.result.modules)
        if total_modules == 0:
            return

        total_coupling = 0.0

        for info in self.result.modules.values():
            # 耦合度 = (出度 + 入度) / (总模块数 - 1)
            degree = len(info.dependencies) + len(info.dependents)
            info.coupling = degree / (total_modules - 1) if total_modules > 1 else 0
            total_coupling += info.coupling

        self.result.avg_coupling = total_coupling / total_modules

    def _detect_cycles(self):
        """检测循环依赖"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            info = self.result.modules.get(node)
            if info:
                for dep in info.dependencies:
                    if dep not in visited:
                        dfs(dep, path)
                    elif dep in rec_stack:
                        # 发现循环
                        cycle_start = path.index(dep)
                        cycle = path[cycle_start:] + [dep]
                        cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for module in self.result.modules:
            if module not in visited:
                dfs(module, [])

        self.result.cycles = cycles

    def _identify_high_coupling(self):
        """识别高耦合模块"""
        self.result.high_coupling_modules = [
            name for name, info in self.result.modules.items()
            if info.coupling > self.threshold
        ]

    def generate_report(self, format_type: str = 'text') -> str:
        """生成报告"""
        if format_type == 'json':
            return self._generate_json_report()
        else:
            return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("依赖分析报告")
        lines.append("=" * 60)
        lines.append("")

        # 概览
        lines.append("【概览】")
        lines.append(f"模块总数: {len(self.result.modules)}")
        lines.append(f"平均耦合度: {self.result.avg_coupling:.2f}")
        lines.append(f"循环依赖数: {len(self.result.cycles)}")
        lines.append("")

        # 高耦合模块
        if self.result.high_coupling_modules:
            lines.append("【高耦合模块】(阈值 > {:.0%})".format(self.threshold))
            for name in sorted(self.result.high_coupling_modules,
                               key=lambda x: self.result.modules[x].coupling,
                               reverse=True):
                info = self.result.modules[name]
                lines.append(f"  {name}: {info.coupling:.2f} "
                           f"(依赖: {len(info.dependencies)}, "
                           f"被依赖: {len(info.dependents)})")
            lines.append("")

        # 循环依赖
        if self.result.cycles:
            lines.append("【循环依赖】")
            for i, cycle in enumerate(self.result.cycles[:5], 1):
                lines.append(f"  {i}. {' -> '.join(cycle)}")
            if len(self.result.cycles) > 5:
                lines.append(f"  ... 还有 {len(self.result.cycles) - 5} 个循环")
            lines.append("")

        # 孤立模块
        isolated = [name for name, info in self.result.modules.items()
                   if not info.dependencies and not info.dependents]
        if isolated:
            lines.append("【孤立模块】")
            for name in isolated:
                lines.append(f"  - {name}")
            lines.append("")

        # 依赖详情
        lines.append("【依赖详情】")
        for name, info in sorted(self.result.modules.items()):
            if info.dependencies or info.dependents:
                lines.append(f"\n  {name}:")
                if info.dependencies:
                    lines.append(f"    依赖: {', '.join(sorted(info.dependencies))}")
                if info.dependents:
                    lines.append(f"    被依赖: {', '.join(sorted(info.dependents))}")

        return '\n'.join(lines)

    def _generate_json_report(self) -> str:
        """生成 JSON 报告"""
        data = {
            'summary': {
                'total_modules': len(self.result.modules),
                'avg_coupling': self.result.avg_coupling,
                'cycle_count': len(self.result.cycles)
            },
            'modules': {
                name: {
                    'dependencies': list(info.dependencies),
                    'dependents': list(info.dependents),
                    'coupling': info.coupling
                }
                for name, info in self.result.modules.items()
            },
            'cycles': self.result.cycles,
            'high_coupling_modules': self.result.high_coupling_modules
        }
        return json.dumps(data, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description='分析项目依赖关系，检测循环依赖和模块耦合度'
    )
    parser.add_argument('--path', '-p', required=True,
                        help='项目路径')
    parser.add_argument('--format', '-f', choices=['text', 'json'],
                        default='text', help='输出格式')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--threshold', '-t', type=float, default=0.3,
                        help='耦合度阈值 (0-1)，默认 0.3')

    args = parser.parse_args()

    # 执行分析
    analyzer = DependencyAnalyzer(args.path, args.threshold)
    result = analyzer.analyze()

    # 生成报告
    report = analyzer.generate_report(args.format)

    # 输出
    if args.output:
        Path(args.output).write_text(report, encoding='utf-8')
        print(f"报告已保存到: {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()
