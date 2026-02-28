#!/usr/bin/env python3
"""
项目架构评估器
检测架构模式、代码组织问题、层间违规

用法:
    python project_architect.py --path ./src --type microservices
    python project_architect.py --path ./src --report html --output report.html
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class IssueLevel(Enum):
    ERROR = "错误"
    WARNING = "警告"
    INFO = "建议"


class ArchitectureType(Enum):
    LAYERED = "layered"
    MICROSERVICES = "microservices"
    MODULAR = "modular"


@dataclass
class ArchitectureIssue:
    """架构问题"""
    level: IssueLevel
    category: str
    message: str
    file_path: str = ""
    suggestion: str = ""


@dataclass
class ArchitectureReport:
    """架构评估报告"""
    architecture_type: ArchitectureType
    detected_layers: List[str] = field(default_factory=list)
    issues: List[ArchitectureIssue] = field(default_factory=list)
    metrics: Dict[str, any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class ProjectArchitect:
    """项目架构评估器"""

    LAYER_PATTERNS = {
        'controller': ['controller', 'api', 'web', 'handler', 'rest', 'resource'],
        'service': ['service', 'business', 'application', 'usecase'],
        'domain': ['domain', 'entity', 'model', 'aggregate', 'valueobject'],
        'repository': ['repository', 'dao', 'mapper', 'persistence', 'data'],
        'infrastructure': ['infrastructure', 'config', 'util', 'common']
    }

    FORBIDDEN_PATTERNS = {
        ArchitectureType.LAYERED: {
            'controller_direct_dao': {
                'from': 'controller',
                'to': 'repository',
                'message': '控制器层直接访问数据访问层，违反分层架构原则',
                'suggestion': '通过 Service 层访问数据'
            }
        },
        ArchitectureType.MICROSERVICES: {
            'direct_db_access': {
                'pattern': r'database|jdbc|jpa|sql',
                'message': '服务间可能存在直接数据库访问',
                'suggestion': '通过 API 调用或消息队列交互'
            }
        }
    }

    def __init__(self, project_path: str, arch_type: ArchitectureType = ArchitectureType.LAYERED):
        self.project_path = Path(project_path)
        self.arch_type = arch_type
        self.report = ArchitectureReport(architecture_type=arch_type)
        self.files_by_layer: Dict[str, List[Path]] = {}

    def analyze(self) -> ArchitectureReport:
        """执行架构评估"""
        self._detect_architecture_type()
        self._classify_files_by_layer()
        self._check_layer_violations()
        self._check_architecture_patterns()
        self._calculate_metrics()
        self._generate_recommendations()
        return self.report

    def _detect_architecture_type(self):
        """检测架构类型"""
        # 检查是否是微服务架构
        service_dirs = []
        for item in self.project_path.iterdir():
            if item.is_dir():
                # 检查是否包含服务特征
                if any((item / f).exists() for f in ['pom.xml', 'build.gradle', 'package.json']):
                    service_dirs.append(item.name)

        if len(service_dirs) > 2:
            self.report.architecture_type = ArchitectureType.MICROSERVICES
            self.report.detected_layers = service_dirs
        else:
            # 检查分层特征
            for layer in self.LAYER_PATTERNS.keys():
                if self._find_layer_files(layer):
                    self.report.detected_layers.append(layer)

            if self.report.detected_layers:
                self.report.architecture_type = ArchitectureType.LAYERED

    def _find_layer_files(self, layer: str) -> bool:
        """查找特定层的文件"""
        patterns = self.LAYER_PATTERNS.get(layer, [])
        for ext in ['*.java', '*.py', '*.ts', '*.js']:
            for file in self.project_path.rglob(ext):
                path_lower = str(file).lower()
                if any(p in path_lower for p in patterns):
                    return True
        return False

    def _classify_files_by_layer(self):
        """按层分类文件"""
        for ext in ['*.java', '*.py', '*.ts', '*.js']:
            for file in self.project_path.rglob(ext):
                if self._should_skip(file):
                    continue

                path_lower = str(file).lower()
                classified = False

                for layer, patterns in self.LAYER_PATTERNS.items():
                    if any(p in path_lower for p in patterns):
                        if layer not in self.files_by_layer:
                            self.files_by_layer[layer] = []
                        self.files_by_layer[layer].append(file)
                        classified = True
                        break

                if not classified:
                    if 'other' not in self.files_by_layer:
                        self.files_by_layer['other'] = []
                    self.files_by_layer['other'].append(file)

    def _should_skip(self, file: Path) -> bool:
        """检查是否应该跳过该文件"""
        skip_patterns = ['node_modules', '__pycache__', '.git', 'target', 'build', 'dist']
        return any(p in str(file) for p in skip_patterns)

    def _check_layer_violations(self):
        """检查层间违规"""
        if self.report.architecture_type == ArchitectureType.LAYERED:
            self._check_layered_violations()
        elif self.report.architecture_type == ArchitectureType.MICROSERVICES:
            self._check_microservices_violations()

    def _check_layered_violations(self):
        """检查分层架构违规"""
        # 检查 Controller 直接访问 Repository
        controllers = self.files_by_layer.get('controller', [])
        repositories = self.files_by_layer.get('repository', [])

        repo_class_names = set()
        for repo_file in repositories:
            content = repo_file.read_text(encoding='utf-8', errors='ignore')
            # 提取类名
            if repo_file.suffix == '.java':
                matches = re.findall(r'(?:class|interface)\s+(\w+)', content)
                repo_class_names.update(matches)

        for ctrl_file in controllers:
            content = ctrl_file.read_text(encoding='utf-8', errors='ignore')
            for repo_class in repo_class_names:
                # 检查是否在 Controller 中实例化或注入 Repository
                if re.search(rf'\b{repo_class}\b', content):
                    self.report.issues.append(ArchitectureIssue(
                        level=IssueLevel.WARNING,
                        category="层间违规",
                        message=f"控制器可能直接访问 Repository: {repo_class}",
                        file_path=str(ctrl_file.relative_to(self.project_path)),
                        suggestion="通过 Service 层访问数据，保持分层清晰"
                    ))

    def _check_microservices_violations(self):
        """检查微服务架构违规"""
        # 检查跨服务直接调用
        for service_name in self.report.detected_layers:
            service_path = self.project_path / service_name
            if not service_path.exists():
                continue

            for file in service_path.rglob('*'):
                if file.is_file():
                    content = file.read_text(encoding='utf-8', errors='ignore')

                    # 检查是否直接访问其他服务的数据库
                    for other_service in self.report.detected_layers:
                        if other_service != service_name:
                            if other_service.lower() in content.lower() and \
                               any(db in content.lower() for db in ['database', 'jdbc', 'sql']):
                                self.report.issues.append(ArchitectureIssue(
                                    level=IssueLevel.ERROR,
                                    category="服务耦合",
                                    message=f"{service_name} 可能直接访问 {other_service} 的数据",
                                    file_path=str(file.relative_to(self.project_path)),
                                    suggestion="通过 API 网关或消息队列进行服务间通信"
                                ))

    def _check_architecture_patterns(self):
        """检查架构模式"""
        # 检查贫血模型
        self._check_anemic_model()

        # 检查上帝类
        self._check_god_classes()

        # 检查重复代码
        self._check_duplicate_patterns()

    def _check_anemic_model(self):
        """检查贫血领域模型"""
        domains = self.files_by_layer.get('domain', [])
        for domain_file in domains:
            content = domain_file.read_text(encoding='utf-8', errors='ignore')

            # 检查是否只有 getter/setter
            class_pattern = r'class\s+(\w+)\s*\{'
            classes = re.findall(class_pattern, content)

            for class_name in classes:
                # 提取类体
                class_match = re.search(rf'class\s+{class_name}\s*\{{(.*?)\n\}}',
                                        content, re.DOTALL)
                if class_match:
                    class_body = class_match.group(1)
                    # 检查是否有业务方法（非 getter/setter）
                    methods = re.findall(r'\b\w+\s+\w+\s*\([^)]*\)', class_body)
                    business_methods = [m for m in methods
                                       if not re.match(r'(?:get|set|is)\w+', m.split()[-1].split('(')[0])]

                    if len(methods) > 0 and len(business_methods) == 0:
                        self.report.issues.append(ArchitectureIssue(
                            level=IssueLevel.WARNING,
                            category="贫血模型",
                            message=f"类 {class_name} 可能为贫血模型（只有 getter/setter）",
                            file_path=str(domain_file.relative_to(self.project_path)),
                            suggestion="将业务逻辑移到领域模型中，实现充血模型"
                        ))

    def _check_god_classes(self):
        """检查上帝类"""
        for layer, files in self.files_by_layer.items():
            for file in files:
                content = file.read_text(encoding='utf-8', errors='ignore')

                # 统计方法数量
                if file.suffix == '.java':
                    methods = len(re.findall(r'(?:public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*\{', content))
                elif file.suffix in ['.py']:
                    methods = len(re.findall(r'def\s+\w+\s*\(', content))
                else:
                    methods = len(re.findall(r'\w+\s*\([^)]*\)\s*\{', content))

                if methods > 20:
                    self.report.issues.append(ArchitectureIssue(
                        level=IssueLevel.WARNING,
                        category="上帝类",
                        message=f"文件包含过多方法 ({methods} 个)",
                        file_path=str(file.relative_to(self.project_path)),
                        suggestion="考虑拆分为多个职责单一的类"
                    ))

    def _check_duplicate_patterns(self):
        """检查重复代码模式"""
        # 简单的重复检测：检查相似的 import 模式
        import_patterns = {}

        for layer, files in self.files_by_layer.items():
            for file in files:
                content = file.read_text(encoding='utf-8', errors='ignore')

                if file.suffix == '.java':
                    imports = tuple(sorted(re.findall(r'import\s+([\w.]+);', content)))
                elif file.suffix == '.py':
                    imports = tuple(sorted(re.findall(r'(?:from|import)\s+([\w.]+)', content)))
                else:
                    continue

                if imports:
                    if imports not in import_patterns:
                        import_patterns[imports] = []
                    import_patterns[imports].append(file)

        # 报告高度相似的文件
        for imports, files in import_patterns.items():
            if len(files) > 2 and len(imports) > 5:
                self.report.issues.append(ArchitectureIssue(
                    level=IssueLevel.INFO,
                    category="潜在重复",
                    message=f"发现 {len(files)} 个文件有相似的依赖模式",
                    suggestion="检查是否存在重复代码或可提取的公共模块"
                ))

    def _calculate_metrics(self):
        """计算架构指标"""
        total_files = sum(len(files) for files in self.files_by_layer.values())

        self.report.metrics = {
            'total_files': total_files,
            'files_by_layer': {layer: len(files) for layer, files in self.files_by_layer.items()},
            'architecture_type': self.report.architecture_type.value,
            'layer_coverage': len(self.report.detected_layers) / len(self.LAYER_PATTERNS),
            'issue_count': {
                'error': len([i for i in self.report.issues if i.level == IssueLevel.ERROR]),
                'warning': len([i for i in self.report.issues if i.level == IssueLevel.WARNING]),
                'info': len([i for i in self.report.issues if i.level == IssueLevel.INFO])
            }
        }

    def _generate_recommendations(self):
        """生成改进建议"""
        recs = []

        # 基于层覆盖率的建议
        if self.report.metrics.get('layer_coverage', 0) < 0.5:
            recs.append("项目分层不够清晰，建议明确划分各层职责")

        # 基于问题数量的建议
        error_count = self.report.metrics.get('issue_count', {}).get('error', 0)
        if error_count > 0:
            recs.append(f"发现 {error_count} 个架构错误，建议优先修复")

        # 基于架构类型的建议
        if self.report.architecture_type == ArchitectureType.MICROSERVICES:
            recs.append("微服务架构建议引入 API 网关统一入口")
            recs.append("建议实施服务注册发现和配置中心")

        self.report.recommendations = recs

    def generate_html_report(self) -> str:
        """生成 HTML 报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>架构评估报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 15px 20px; background: #f8f9fa; border-radius: 4px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        .issue {{ margin: 10px 0; padding: 15px; border-left: 4px solid #ddd; background: #fafafa; }}
        .issue.error {{ border-left-color: #f44336; background: #ffebee; }}
        .issue.warning {{ border-left-color: #ff9800; background: #fff3e0; }}
        .issue.info {{ border-left-color: #2196F3; background: #e3f2fd; }}
        .issue-level {{ font-size: 12px; font-weight: bold; text-transform: uppercase; }}
        .issue.error .issue-level {{ color: #f44336; }}
        .issue.warning .issue-level {{ color: #ff9800; }}
        .issue.info .issue-level {{ color: #2196F3; }}
        .issue-category {{ font-weight: bold; color: #333; }}
        .issue-file {{ font-family: monospace; font-size: 12px; color: #666; }}
        .recommendation {{ padding: 10px 15px; background: #e8f5e9; border-radius: 4px; margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>架构评估报告</h1>

        <h2>概览</h2>
        <div class="metric">
            <div class="metric-value">{self.report.metrics.get('total_files', 0)}</div>
            <div class="metric-label">总文件数</div>
        </div>
        <div class="metric">
            <div class="metric-value">{self.report.architecture_type.value}</div>
            <div class="metric-label">架构类型</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(self.report.detected_layers)}</div>
            <div class="metric-label">检测到的层</div>
        </div>

        <h2>问题统计</h2>
        <div class="metric">
            <div class="metric-value" style="color: #f44336;">{self.report.metrics.get('issue_count', {}).get('error', 0)}</div>
            <div class="metric-label">错误</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #ff9800;">{self.report.metrics.get('issue_count', {}).get('warning', 0)}</div>
            <div class="metric-label">警告</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: #2196F3;">{self.report.metrics.get('issue_count', {}).get('info', 0)}</div>
            <div class="metric-label">建议</div>
        </div>

        <h2>分层分布</h2>
        <table>
            <tr><th>层级</th><th>文件数</th></tr>
"""
        for layer, count in self.report.metrics.get('files_by_layer', {}).items():
            html += f"            <tr><td>{layer}</td><td>{count}</td></tr>\n"

        html += """
        </table>

        <h2>发现的问题</h2>
"""

        for issue in self.report.issues:
            level_class = issue.level.name.lower()
            html += f"""
        <div class="issue {level_class}">
            <div class="issue-level">{issue.level.value}</div>
            <div class="issue-category">{issue.category}</div>
            <div>{issue.message}</div>
            {f'<div class="issue-file">{issue.file_path}</div>' if issue.file_path else ''}
            {f'<div><strong>建议:</strong> {issue.suggestion}</div>' if issue.suggestion else ''}
        </div>
"""

        html += """
        <h2>改进建议</h2>
"""
        for rec in self.report.recommendations:
            html += f'        <div class="recommendation">{rec}</div>\n'

        html += """
    </div>
</body>
</html>
"""
        return html


def main():
    parser = argparse.ArgumentParser(
        description='评估项目架构，检测架构模式和代码组织问题'
    )
    parser.add_argument('--path', '-p', required=True, help='项目路径')
    parser.add_argument('--type', '-t',
                        choices=['layered', 'microservices', 'modular'],
                        default='layered', help='架构类型')
    parser.add_argument('--report', '-r',
                        choices=['text', 'json', 'html'],
                        default='text', help='报告格式')
    parser.add_argument('--output', '-o', help='输出文件')

    args = parser.parse_args()

    arch_type = ArchitectureType(args.type)
    architect = ProjectArchitect(args.path, arch_type)
    report = architect.analyze()

    if args.report == 'html':
        output = architect.generate_html_report()
    elif args.report == 'json':
        output = json.dumps({
            'architecture_type': report.architecture_type.value,
            'detected_layers': report.detected_layers,
            'metrics': report.metrics,
            'issues': [
                {
                    'level': i.level.value,
                    'category': i.category,
                    'message': i.message,
                    'file': i.file_path,
                    'suggestion': i.suggestion
                }
                for i in report.issues
            ],
            'recommendations': report.recommendations
        }, indent=2, ensure_ascii=False)
    else:
        # Text report
        lines = []
        lines.append("=" * 60)
        lines.append("架构评估报告")
        lines.append("=" * 60)
        lines.append(f"\n架构类型: {report.architecture_type.value}")
        lines.append(f"检测到的层: {', '.join(report.detected_layers)}")
        lines.append("\n【指标】")
        for k, v in report.metrics.items():
            lines.append(f"  {k}: {v}")

        lines.append("\n【问题列表】")
        for issue in report.issues:
            lines.append(f"\n[{issue.level.value}] {issue.category}")
            lines.append(f"  {issue.message}")
            if issue.file_path:
                lines.append(f"  文件: {issue.file_path}")
            if issue.suggestion:
                lines.append(f"  建议: {issue.suggestion}")

        lines.append("\n【改进建议】")
        for rec in report.recommendations:
            lines.append(f"  - {rec}")

        output = '\n'.join(lines)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"报告已保存到: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
