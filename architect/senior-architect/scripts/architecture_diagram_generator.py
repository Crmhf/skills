#!/usr/bin/env python3
"""
架构图生成器
从项目结构自动生成 Mermaid/PlantUML/ASCII 架构图

用法:
    python architecture_diagram_generator.py --path ./src --format mermaid
    python architecture_diagram_generator.py --path ./src --format plantuml --output architecture.puml
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class Module:
    """模块信息"""
    name: str
    path: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)


@dataclass
class ProjectStructure:
    """项目结构"""
    modules: Dict[str, Module] = field(default_factory=dict)
    layers: Dict[str, List[str]] = field(default_factory=dict)


class ProjectAnalyzer:
    """项目分析器"""

    LAYER_PATTERNS = {
        'controller': ['controller', 'api', 'web', 'handler', 'resource'],
        'service': ['service', 'business', 'domain', 'core'],
        'repository': ['repository', 'dao', 'mapper', 'data', 'persistence'],
        'entity': ['entity', 'model', 'dto', 'vo', 'po'],
        'config': ['config', 'configuration', 'settings'],
        'util': ['util', 'utils', 'common', 'shared', 'helper']
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.structure = ProjectStructure()

    def analyze(self) -> ProjectStructure:
        """分析项目结构"""
        self._scan_modules()
        self._analyze_dependencies()
        self._classify_layers()
        return self.structure

    def _scan_modules(self):
        """扫描模块"""
        # 检测项目类型
        if self._is_java_project():
            self._scan_java_modules()
        elif self._is_python_project():
            self._scan_python_modules()
        elif self._is_js_project():
            self._scan_js_modules()
        else:
            self._scan_generic_modules()

    def _is_java_project(self) -> bool:
        return any(self.project_path.glob('pom.xml')) or \
               any(self.project_path.glob('build.gradle'))

    def _is_python_project(self) -> bool:
        return any(self.project_path.glob('requirements.txt')) or \
               any(self.project_path.glob('pyproject.toml')) or \
               any(self.project_path.glob('setup.py'))

    def _is_js_project(self) -> bool:
        return any(self.project_path.glob('package.json'))

    def _scan_java_modules(self):
        """扫描 Java 模块"""
        src_path = self.project_path / 'src' / 'main' / 'java'
        if not src_path.exists():
            src_path = self.project_path

        for java_file in src_path.rglob('*.java'):
            content = java_file.read_text(encoding='utf-8', errors='ignore')

            # 提取类名
            class_match = re.search(r'(?:class|interface|enum)\s+(\w+)', content)
            if class_match:
                class_name = class_match.group(1)
                module = Module(
                    name=class_name,
                    path=str(java_file.relative_to(self.project_path))
                )

                # 提取 import
                imports = re.findall(r'import\s+([\w.]+);', content)
                module.imports = imports

                self.structure.modules[class_name] = module

    def _scan_python_modules(self):
        """扫描 Python 模块"""
        for py_file in self.project_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            content = py_file.read_text(encoding='utf-8', errors='ignore')
            module_name = py_file.stem

            module = Module(
                name=module_name,
                path=str(py_file.relative_to(self.project_path))
            )

            # 提取 import
            imports = re.findall(r'(?:from|import)\s+([\w.]+)', content)
            module.imports = imports

            self.structure.modules[module_name] = module

    def _scan_js_modules(self):
        """扫描 JavaScript/TypeScript 模块"""
        for ext in ['*.js', '*.ts', '*.jsx', '*.tsx']:
            for js_file in self.project_path.rglob(ext):
                if 'node_modules' in str(js_file):
                    continue

                content = js_file.read_text(encoding='utf-8', errors='ignore')
                module_name = js_file.stem

                module = Module(
                    name=module_name,
                    path=str(js_file.relative_to(self.project_path))
                )

                # 提取 import/require
                imports = re.findall(r'(?:import|require)\s*\(?[\'"]([^\'"]+)', content)
                module.imports = imports

                self.structure.modules[module_name] = module

    def _scan_generic_modules(self):
        """通用模块扫描"""
        # 按目录结构识别模块
        for item in self.project_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                module = Module(
                    name=item.name,
                    path=str(item.relative_to(self.project_path))
                )
                self.structure.modules[item.name] = module

    def _analyze_dependencies(self):
        """分析模块依赖"""
        for name, module in self.structure.modules.items():
            for imp in module.imports:
                # 查找被依赖的模块
                for other_name, other_module in self.structure.modules.items():
                    if other_name != name and other_name in imp:
                        module.dependencies.add(other_name)

    def _classify_layers(self):
        """按分层架构分类"""
        for name, module in self.structure.modules.items():
            path_lower = module.path.lower()
            classified = False

            for layer, patterns in self.LAYER_PATTERNS.items():
                if any(p in path_lower for p in patterns):
                    if layer not in self.structure.layers:
                        self.structure.layers[layer] = []
                    self.structure.layers[layer].append(name)
                    classified = True
                    break

            if not classified:
                if 'other' not in self.structure.layers:
                    self.structure.layers['other'] = []
                self.structure.layers['other'].append(name)


class DiagramGenerator:
    """图表生成器"""

    def __init__(self, structure: ProjectStructure):
        self.structure = structure

    def generate(self, format_type: str) -> str:
        """生成图表"""
        if format_type == 'mermaid':
            return self._generate_mermaid()
        elif format_type == 'plantuml':
            return self._generate_plantuml()
        elif format_type == 'ascii':
            return self._generate_ascii()
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _generate_mermaid(self) -> str:
        """生成 Mermaid 图表"""
        lines = ['graph TD']

        # 按层生成节点
        for layer, modules in self.structure.layers.items():
            if modules:
                lines.append(f'    subgraph {layer.title()}')
                for module_name in modules:
                    lines.append(f'        {self._safe_id(module_name)}[{module_name}]')
                lines.append('    end')

        # 生成依赖关系
        for name, module in self.structure.modules.items():
            for dep in module.dependencies:
                if dep in self.structure.modules:
                    lines.append(f'    {self._safe_id(name)} --> {self._safe_id(dep)}')

        return '\n'.join(lines)

    def _generate_plantuml(self) -> str:
        """生成 PlantUML 图表"""
        lines = ['@startuml', '']

        # 定义包
        for layer, modules in self.structure.layers.items():
            if modules:
                lines.append(f'package "{layer.title()}" {{')
                for module_name in modules:
                    lines.append(f'    class {module_name}')
                lines.append('}')
                lines.append('')

        # 生成依赖关系
        for name, module in self.structure.modules.items():
            for dep in module.dependencies:
                if dep in self.structure.modules:
                    lines.append(f'{name} --> {dep}')

        lines.append('')
        lines.append('@enduml')

        return '\n'.join(lines)

    def _generate_ascii(self) -> str:
        """生成 ASCII 图表"""
        lines = ['Project Architecture:', '=' * 50, '']

        # 简单的文本层次展示
        for layer, modules in self.structure.layers.items():
            if modules:
                lines.append(f'[{layer.upper()}]')
                for module_name in modules[:5]:  # 限制显示数量
                    lines.append(f'  └─ {module_name}')
                if len(modules) > 5:
                    lines.append(f'  └─ ... and {len(modules) - 5} more')
                lines.append('')

        return '\n'.join(lines)

    def _safe_id(self, name: str) -> str:
        """生成安全的 ID"""
        return re.sub(r'[^\w]', '_', name)


def main():
    parser = argparse.ArgumentParser(
        description='从项目结构生成架构图'
    )
    parser.add_argument('--path', '-p', required=True,
                        help='项目路径')
    parser.add_argument('--format', '-f', choices=['mermaid', 'plantuml', 'ascii'],
                        default='mermaid', help='输出格式')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--layer-filter', '-l',
                        help='只显示特定层，逗号分隔')

    args = parser.parse_args()

    # 分析项目
    analyzer = ProjectAnalyzer(args.path)
    structure = analyzer.analyze()

    print(f"发现 {len(structure.modules)} 个模块")
    print(f"分层分布: {', '.join(f'{k}={len(v)}' for k, v in structure.layers.items())}")

    # 生成图表
    generator = DiagramGenerator(structure)
    diagram = generator.generate(args.format)

    # 输出
    if args.output:
        Path(args.output).write_text(diagram, encoding='utf-8')
        print(f"图表已保存到: {args.output}")
    else:
        print("\n" + "=" * 50)
        print(diagram)


if __name__ == '__main__':
    main()
