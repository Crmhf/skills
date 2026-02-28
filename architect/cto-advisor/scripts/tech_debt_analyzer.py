#!/usr/bin/env python3
"""
技术债务分析器
识别技术债务、计算偿还成本、制定偿还计划

用法:
    python tech_debt_analyzer.py --path ./src
    python tech_debt_analyzer.py --path ./src --sonar-url http://sonar.internal --report html
"""

import os
import re
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class DebtType(Enum):
    CODE = "代码债务"
    ARCHITECTURE = "架构债务"
    TEST = "测试债务"
    DOCUMENTATION = "文档债务"
    INFRASTRUCTURE = "基础设施债务"
    DEPENDENCY = "依赖债务"


class DebtPriority(Enum):
    CRITICAL = "P0-严重"
    HIGH = "P1-高"
    MEDIUM = "P2-中"
    LOW = "P3-低"


@dataclass
class TechDebtItem:
    """技术债务项"""
    debt_type: DebtType
    priority: DebtPriority
    description: str
    file_path: str
    line_number: int = 0
    estimated_effort: int = 0  # 人时
    business_impact: str = ""
    suggestion: str = ""


@dataclass
class TechDebtReport:
    """技术债务报告"""
    summary: Dict[str, any] = field(default_factory=dict)
    debts: List[TechDebtItem] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class TechDebtAnalyzer:
    """技术债务分析器"""

    # 代码异味模式
    CODE_SMELLS = {
        'long_method': {
            'pattern': r'(?:public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*\{',
            'threshold': 50,  # 行数
            'type': DebtType.CODE,
            'priority': DebtPriority.MEDIUM
        },
        'todo_comment': {
            'pattern': r'(?:TODO|FIXME|HACK|XXX)',
            'type': DebtType.CODE,
            'priority': DebtPriority.LOW
        },
        'hardcoded_value': {
            'pattern': r'(?:password|secret|key)\s*=\s*["\'][^"\']+["\']',
            'type': DebtType.CODE,
            'priority': DebtPriority.CRITICAL
        }
    }

    def __init__(self, project_path: str, sonar_url: str = None):
        self.project_path = Path(project_path)
        self.sonar_url = sonar_url
        self.report = TechDebtReport()

    def analyze(self) -> TechDebtReport:
        """执行技术债务分析"""
        self._analyze_code_debt()
        self._analyze_test_debt()
        self._analyze_doc_debt()
        self._analyze_infrastructure_debt()
        self._analyze_dependency_debt()

        if self.sonar_url:
            self._fetch_sonarqube_data()

        self._calculate_summary()
        self._generate_recommendations()
        return self.report

    def _analyze_code_debt(self):
        """分析代码债务"""
        for file_path in self._get_source_files():
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')

            # 检查长方法
            self._check_long_methods(file_path, lines)

            # 检查 TODO/FIXME
            self._check_todo_comments(file_path, lines)

            # 检查硬编码
            self._check_hardcoded_values(file_path, lines)

            # 检查重复代码（简单模式匹配）
            self._check_duplicate_patterns(file_path, lines)

    def _get_source_files(self) -> List[Path]:
        """获取源代码文件"""
        files = []
        extensions = ['*.java', '*.py', '*.js', '*.ts', '*.go', '*.cpp', '*.c']

        for ext in extensions:
            for file in self.project_path.rglob(ext):
                if not any(skip in str(file) for skip in ['node_modules', '__pycache__', '.git', 'vendor']):
                    files.append(file)

        return files

    def _check_long_methods(self, file_path: Path, lines: List[str]):
        """检查长方法"""
        in_method = False
        method_start = 0
        brace_count = 0

        for i, line in enumerate(lines):
            if not in_method:
                if re.match(r'^(?:public|private|protected|func|def)', line.strip()):
                    in_method = True
                    method_start = i
                    brace_count = line.count('{') - line.count('}')
            else:
                brace_count += line.count('{') - line.count('}')

                if brace_count == 0:
                    method_length = i - method_start + 1
                    if method_length > 50:
                        self.report.debts.append(TechDebtItem(
                            debt_type=DebtType.CODE,
                            priority=DebtPriority.MEDIUM,
                            description=f"方法过长 ({method_length} 行)",
                            file_path=str(file_path.relative_to(self.project_path)),
                            line_number=method_start + 1,
                            estimated_effort=method_length // 10,
                            business_impact="维护困难，测试覆盖率低",
                            suggestion="提取子方法，单一职责原则"
                        ))
                    in_method = False

    def _check_todo_comments(self, file_path: Path, lines: List[str]):
        """检查 TODO/FIXME 注释"""
        for i, line in enumerate(lines):
            match = re.search(r'(?:TODO|FIXME|HACK|XXX)[\s:]*(.*)', line, re.IGNORECASE)
            if match:
                self.report.debts.append(TechDebtItem(
                    debt_type=DebtType.CODE,
                    priority=DebtPriority.LOW,
                    description=f"待办事项: {match.group(1).strip()[:50]}",
                    file_path=str(file_path.relative_to(self.project_path)),
                    line_number=i + 1,
                    estimated_effort=4,
                    business_impact="技术债务累积",
                    suggestion="安排迭代清理"
                ))

    def _check_hardcoded_values(self, file_path: Path, lines: List[str]):
        """检查硬编码值"""
        for i, line in enumerate(lines):
            if re.search(r'(?:password|secret|key|token)\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                self.report.debts.append(TechDebtItem(
                    debt_type=DebtType.CODE,
                    priority=DebtPriority.CRITICAL,
                    description="硬编码敏感信息",
                    file_path=str(file_path.relative_to(self.project_path)),
                    line_number=i + 1,
                    estimated_effort=2,
                    business_impact="安全风险",
                    suggestion="使用配置中心或密钥管理服务"
                ))

    def _check_duplicate_patterns(self, file_path: Path, lines: List[str]):
        """检查重复代码模式（简化版）"""
        # 检查重复的空 catch 块
        content = '\n'.join(lines)
        if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', content):
            self.report.debts.append(TechDebtItem(
                debt_type=DebtType.CODE,
                priority=DebtPriority.HIGH,
                description="空异常处理块",
                file_path=str(file_path.relative_to(self.project_path)),
                estimated_effort=1,
                business_impact="异常被静默吞没",
                suggestion="添加日志或重新抛出异常"
            ))

    def _analyze_test_debt(self):
        """分析测试债务"""
        test_files = list(self.project_path.rglob('*Test*.java')) + \
                     list(self.project_path.rglob('test_*.py')) + \
                     list(self.project_path.rglob('*.test.js'))

        source_files = self._get_source_files()

        test_ratio = len(test_files) / len(source_files) if source_files else 0

        if test_ratio < 0.5:
            self.report.debts.append(TechDebtItem(
                debt_type=DebtType.TEST,
                priority=DebtPriority.HIGH,
                description=f"测试覆盖率低 (测试/源码比: {test_ratio:.1%})",
                file_path="project",
                estimated_effort=len(source_files) * 2,
                business_impact="回归成本高，Bug 逃逸率高",
                suggestion="制定测试策略，优先覆盖核心流程"
            ))

    def _analyze_doc_debt(self):
        """分析文档债务"""
        readme_exists = (self.project_path / 'README.md').exists()
        api_doc_exists = any(self.project_path.rglob('*.md'))

        if not readme_exists:
            self.report.debts.append(TechDebtItem(
                debt_type=DebtType.DOCUMENTATION,
                priority=DebtPriority.MEDIUM,
                description="缺少 README 文档",
                file_path="project",
                estimated_effort=4,
                business_impact="新人上手困难",
                suggestion="创建项目 README，包含架构图和开发指南"
            ))

        # 检查 API 文档
        api_files = list(self.project_path.rglob('*Controller*.java')) + \
                    list(self.project_path.rglob('*Handler*.go'))

        for api_file in api_files[:5]:  # 采样检查
            content = api_file.read_text(encoding='utf-8', errors='ignore')
            if '@Api' not in content and '@Swagger' not in content and 'swagger' not in content.lower():
                self.report.debts.append(TechDebtItem(
                    debt_type=DebtType.DOCUMENTATION,
                    priority=DebtPriority.LOW,
                    description=f"API 缺少文档注释: {api_file.name}",
                    file_path=str(api_file.relative_to(self.project_path)),
                    estimated_effort=2,
                    business_impact="API 使用困难",
                    suggestion="添加 Swagger/OpenAPI 注解"
                ))

    def _analyze_infrastructure_debt(self):
        """分析基础设施债务"""
        has_ci = any([
            (self.project_path / '.github' / 'workflows').exists(),
            (self.project_path / '.gitlab-ci.yml').exists(),
            (self.project_path / 'Jenkinsfile').exists()
        ])

        has_docker = (self.project_path / 'Dockerfile').exists()

        if not has_ci:
            self.report.debts.append(TechDebtItem(
                debt_type=DebtType.INFRASTRUCTURE,
                priority=DebtPriority.CRITICAL,
                description="缺少 CI/CD 流水线",
                file_path="project",
                estimated_effort=16,
                business_impact="手动部署风险高，交付效率低",
                suggestion="搭建 GitHub Actions / GitLab CI 流水线"
            ))

        if not has_docker:
            self.report.debts.append(TechDebtItem(
                debt_type=DebtType.INFRASTRUCTURE,
                priority=DebtPriority.HIGH,
                description="未容器化部署",
                file_path="project",
                estimated_effort=8,
                business_impact="环境一致性差，部署复杂",
                suggestion="添加 Dockerfile 和 docker-compose"
            ))

    def _analyze_dependency_debt(self):
        """分析依赖债务"""
        # 检查 Java 项目
        pom_file = self.project_path / 'pom.xml'
        if pom_file.exists():
            content = pom_file.read_text(encoding='utf-8', errors='ignore')
            # 检查 Spring Boot 版本
            if '<version>2.0' in content or '<version>2.1' in content:
                self.report.debts.append(TechDebtItem(
                    debt_type=DebtType.DEPENDENCY,
                    priority=DebtPriority.HIGH,
                    description="Spring Boot 版本过旧 (2.0/2.1 已 EOL)",
                    file_path="pom.xml",
                    estimated_effort=40,
                    business_impact="安全风险，无法获得更新",
                    suggestion="升级到 Spring Boot 3.x"
                ))

        # 检查 Python 项目
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists():
            content = req_file.read_text(encoding='utf-8', errors='ignore')
            # 检查 Django 版本
            django_match = re.search(r'Django==([\d.]+)', content)
            if django_match:
                version = django_match.group(1)
                if version.startswith('2.') or version.startswith('3.0'):
                    self.report.debts.append(TechDebtItem(
                        debt_type=DebtType.DEPENDENCY,
                        priority=DebtPriority.MEDIUM,
                        description=f"Django 版本过旧 ({version})",
                        file_path="requirements.txt",
                        estimated_effort=16,
                        business_impact="缺少新功能和安全更新",
                        suggestion="升级到 Django 4.x"
                    ))

        # 检查 Node.js 项目
        package_file = self.project_path / 'package.json'
        if package_file.exists():
            content = package_file.read_text(encoding='utf-8', errors='ignore')
            # 检查是否有安全审计
            if '"audit"' not in content and 'npm audit' not in content:
                self.report.debts.append(TechDebtItem(
                    debt_type=DebtType.DEPENDENCY,
                    priority=DebtPriority.MEDIUM,
                    description="未配置依赖安全审计",
                    file_path="package.json",
                    estimated_effort=2,
                    business_impact="安全漏洞风险",
                    suggestion="添加 npm audit 到 CI 流程"
                ))

    def _fetch_sonarqube_data(self):
        """从 SonarQube 获取数据"""
        # 这里可以集成 SonarQube API
        pass

    def _calculate_summary(self):
        """计算汇总信息"""
        debt_by_type = {}
        debt_by_priority = {}
        total_effort = 0

        for debt in self.report.debts:
            debt_by_type[debt.debt_type.value] = debt_by_type.get(debt.debt_type.value, 0) + 1
            debt_by_priority[debt.priority.value] = debt_by_priority.get(debt.priority.value, 0) + 1
            total_effort += debt.estimated_effort

        # 计算债务比率（简化计算）
        source_files = len(self._get_source_files())
        debt_ratio = min(100, (len(self.report.debts) / max(source_files, 1)) * 10)

        self.report.summary = {
            'total_debts': len(self.report.debts),
            'total_effort_hours': total_effort,
            'total_effort_days': round(total_effort / 8, 1),
            'debt_by_type': debt_by_type,
            'debt_by_priority': debt_by_priority,
            'debt_ratio_percent': round(debt_ratio, 1),
            'health_level': self._get_health_level(debt_ratio),
            'analysis_date': datetime.now().isoformat()
        }

    def _get_health_level(self, ratio: float) -> str:
        """获取健康等级"""
        if ratio < 5:
            return "健康 🟢"
        elif ratio < 10:
            return "可控 🟡"
        elif ratio < 20:
            return "需关注 🟠"
        else:
            return "危险 🔴"

    def _generate_recommendations(self):
        """生成改进建议"""
        recs = []

        # 基于优先级生成建议
        critical_count = self.report.summary.get('debt_by_priority', {}).get('P0-严重', 0)
        if critical_count > 0:
            recs.append(f"【紧急】有 {critical_count} 个严重技术债务需立即处理")

        # 基于类型生成建议
        if self.report.summary.get('debt_by_type', {}).get('基础设施债务', 0) > 0:
            recs.append("建议优先完善 CI/CD 和容器化部署")

        if self.report.summary.get('debt_by_type', {}).get('测试债务', 0) > 0:
            recs.append("建议制定测试策略，建立质量门禁")

        # 通用建议
        recs.append("建议采用 '20% 规则'：每个迭代预留 20% 时间偿还技术债务")
        recs.append("建议建立代码审查规范，预防新增技术债务")

        self.report.recommendations = recs

    def generate_text_report(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("技术债务分析报告")
        lines.append("=" * 60)
        lines.append("")

        # 汇总
        summary = self.report.summary
        lines.append("【汇总】")
        lines.append(f"债务总数: {summary.get('total_debts', 0)}")
        lines.append(f"预估工作量: {summary.get('total_effort_days', 0)} 人天")
        lines.append(f"债务比率: {summary.get('debt_ratio_percent', 0)}%")
        lines.append(f"健康等级: {summary.get('health_level', '未知')}")
        lines.append("")

        # 按类型分布
        lines.append("【按类型分布】")
        for debt_type, count in summary.get('debt_by_type', {}).items():
            lines.append(f"  {debt_type}: {count}")
        lines.append("")

        # 按优先级分布
        lines.append("【按优先级分布】")
        for priority, count in summary.get('debt_by_priority', {}).items():
            lines.append(f"  {priority}: {count}")
        lines.append("")

        # 详细债务列表
        lines.append("【详细债务列表】")
        for debt in sorted(self.report.debts, key=lambda x: x.priority.value):
            lines.append(f"\n[{debt.priority.value}] {debt.debt_type.value}")
            lines.append(f"  描述: {debt.description}")
            lines.append(f"  文件: {debt.file_path}" + (f":{debt.line_number}" if debt.line_number else ""))
            lines.append(f"  预估工作量: {debt.estimated_effort} 小时")
            lines.append(f"  业务影响: {debt.business_impact}")
            lines.append(f"  建议: {debt.suggestion}")

        # 改进建议
        lines.append("\n【改进建议】")
        for i, rec in enumerate(self.report.recommendations, 1):
            lines.append(f"  {i}. {rec}")

        return '\n'.join(lines)

    def generate_html_report(self) -> str:
        """生成 HTML 报告"""
        summary = self.report.summary

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>技术债务分析报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white;
                      padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 15px 20px;
                   background: #f8f9fa; border-radius: 4px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        .debt {{ margin: 10px 0; padding: 15px; border-left: 4px solid #ddd;
                 background: #fafafa; }}
        .debt.P0-严重 {{ border-left-color: #e74c3c; background: #ffebee; }}
        .debt.P1-高 {{ border-left-color: #f39c12; background: #fff3e0; }}
        .debt.P2-中 {{ border-left-color: #3498db; background: #e3f2fd; }}
        .debt.P3-低 {{ border-left-color: #95a5a6; background: #f5f5f5; }}
        .debt-type {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .debt-priority {{ font-weight: bold; }}
        .recommendation {{ padding: 10px 15px; background: #e8f5e9;
                          border-radius: 4px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>技术债务分析报告</h1>
        <p>分析时间: {summary.get('analysis_date', '')}</p>

        <h2>汇总</h2>
        <div class="metric">
            <div class="metric-value">{summary.get('total_debts', 0)}</div>
            <div class="metric-label">债务总数</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary.get('total_effort_days', 0)}</div>
            <div class="metric-label">预估工作量(人天)</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary.get('debt_ratio_percent', 0)}%</div>
            <div class="metric-label">债务比率</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="font-size: 18px;">{summary.get('health_level', '未知')}</div>
            <div class="metric-label">健康等级</div>
        </div>

        <h2>债务列表</h2>
"""
        for debt in sorted(self.report.debts, key=lambda x: x.priority.value):
            html += f"""
        <div class="debt {debt.priority.value}">
            <div class="debt-type">{debt.debt_type.value}</div>
            <div class="debt-priority">{debt.priority.value}</div>
            <div>{debt.description}</div>
            <div style="color: #666; font-size: 12px;">
                文件: {debt.file_path} 行号: {debt.line_number or 'N/A'}
            </div>
            <div style="color: #666; font-size: 12px;">
                预估工作量: {debt.estimated_effort} 小时 | 业务影响: {debt.business_impact}
            </div>
            <div style="color: #27ae60; font-size: 12px;">建议: {debt.suggestion}</div>
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
    parser = argparse.ArgumentParser(description='分析项目技术债务')
    parser.add_argument('--path', '-p', required=True, help='项目路径')
    parser.add_argument('--sonar-url', help='SonarQube URL')
    parser.add_argument('--format', '-f', choices=['text', 'html', 'json'],
                        default='text', help='报告格式')
    parser.add_argument('--output', '-o', help='输出文件')

    args = parser.parse_args()

    # 执行分析
    analyzer = TechDebtAnalyzer(args.path, args.sonar_url)
    report = analyzer.analyze()

    # 生成报告
    if args.format == 'html':
        output = analyzer.generate_html_report()
    elif args.format == 'json':
        output = json.dumps({
            'summary': report.summary,
            'debts': [
                {
                    'type': d.debt_type.value,
                    'priority': d.priority.value,
                    'description': d.description,
                    'file': d.file_path,
                    'line': d.line_number,
                    'effort': d.estimated_effort,
                    'impact': d.business_impact,
                    'suggestion': d.suggestion
                }
                for d in report.debts
            ],
            'recommendations': report.recommendations
        }, indent=2, ensure_ascii=False)
    else:
        output = analyzer.generate_text_report()

    # 输出
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"报告已保存到: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
