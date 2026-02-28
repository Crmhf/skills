#!/usr/bin/env python3
"""
团队扩展计算器
计算团队规模规划、招聘节奏、预算评估、风险评估

用法:
    python team_scaling_calculator.py --current 20 --target 50 --months 12
    python team_scaling_calculator.py --current 15 --target 40 --months 9 --output plan.json
"""

import json
import argparse
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime, timedelta


@dataclass
class ScalingPhase:
    """扩展阶段"""
    name: str
    month: int
    team_size: int
    new_hires: int
    productivity_factor: float
    effective_output: float
    key_actions: List[str] = field(default_factory=list)


@dataclass
class ScalingPlan:
    """扩展计划"""
    current_size: int
    target_size: int
    duration_months: int
    phases: List[ScalingPhase] = field(default_factory=list)
    risks: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


class TeamScalingCalculator:
    """团队扩展计算器"""

    # 新员工入职产出系数（按月）
    ONBOARDING_CURVE = {
        1: 0.1,   # 第1月：熟悉环境
        2: 0.3,   # 第2月：开始贡献
        3: 0.6,   # 第3月：基本独立
        4: 0.8,   # 第4月：接近满产
        5: 0.9,
        6: 0.95   # 6月后：满产
    }

    # 沟通成本系数（基于团队规模）
    COMMUNICATION_OVERHEAD = {
        5: 1.0,
        10: 0.95,
        20: 0.88,
        30: 0.80,
        50: 0.70,
        100: 0.60
    }

    def __init__(self, current_size: int, target_size: int, months: int,
                 current_productivity: float = 100.0, onboarding_months: int = 3):
        self.current_size = current_size
        self.target_size = target_size
        self.months = months
        self.current_productivity = current_productivity
        self.onboarding_months = onboarding_months
        self.plan = ScalingPlan(
            current_size=current_size,
            target_size=target_size,
            duration_months=months
        )

    def calculate(self) -> ScalingPlan:
        """计算扩展计划"""
        self._calculate_phases()
        self._calculate_risks()
        self._generate_recommendations()
        self._calculate_summary()
        return self.plan

    def _calculate_phases(self):
        """计算各阶段计划"""
        total_new_hires = self.target_size - self.current_size
        hires_per_month = total_new_hires / self.months

        current_size = self.current_size
        cumulative_output = 0
        baseline_output = self.current_size * self.current_productivity

        # 按季度划分阶段
        phase_names = ['启动期', '加速期', '稳定期', '优化期']
        phase_months = [3, 3, 3, max(0, self.months - 9)]

        month = 0
        for phase_idx, phase_duration in enumerate(phase_months):
            if phase_duration <= 0:
                continue

            phase_hires = hires_per_month * phase_duration
            phase_new_hires = round(phase_hires)

            # 计算该阶段每月的人员变化
            monthly_hires = phase_new_hires / phase_duration if phase_duration > 0 else 0

            for m in range(phase_duration):
                month += 1
                if month > self.months:
                    break

                # 本月新入职人数
                hires_this_month = round(monthly_hires)
                current_size += hires_this_month

                # 计算本月有效产出
                effective_output = self._calculate_monthly_output(
                    current_size, hires_this_month, month
                )
                cumulative_output += effective_output

                # 只在阶段结束时记录
                if m == phase_duration - 1 or month == self.months:
                    productivity_factor = effective_output / (current_size * self.current_productivity)

                    phase = ScalingPhase(
                        name=phase_names[min(phase_idx, len(phase_names)-1)],
                        month=month,
                        team_size=current_size,
                        new_hires=phase_new_hires if m == phase_duration - 1 else 0,
                        productivity_factor=round(productivity_factor, 2),
                        effective_output=round(effective_output, 1),
                        key_actions=self._get_phase_actions(phase_idx, current_size)
                    )
                    self.plan.phases.append(phase)

    def _calculate_monthly_output(self, team_size: int, new_hires: int, month: int) -> float:
        """计算月度产出"""
        # 老员工产出
        existing_size = team_size - new_hires
        existing_output = existing_size * self.current_productivity

        # 新员工产出（按入职曲线）
        new_hire_output = 0
        for i in range(new_hires):
            # 假设新人是均匀入职的
            onboard_progress = min(month, self.onboarding_months)
            new_hire_output += self.current_productivity * self.ONBOARDING_CURVE.get(onboard_progress, 0.95)

        total_output = existing_output + new_hire_output

        # 应用沟通成本系数
        comm_factor = self._get_communication_factor(team_size)
        adjusted_output = total_output * comm_factor

        return adjusted_output

    def _get_communication_factor(self, team_size: int) -> float:
        """获取沟通成本系数"""
        for size, factor in sorted(self.COMMUNICATION_OVERHEAD.items()):
            if team_size <= size:
                return factor
        return 0.55  # 超大规模团队

    def _get_phase_actions(self, phase_idx: int, team_size: int) -> List[str]:
        """获取阶段关键行动"""
        actions = {
            0: [  # 启动期
                "建立招聘流程和 JD",
                "搭建入职培训体系",
                "确定技术文档基线",
                "设置导师制度"
            ],
            1: [  # 加速期
                "引入 Tech Lead 角色",
                "拆分为小团队",
                "完善代码审查流程",
                "建立周会机制"
            ],
            2: [  # 稳定期
                "优化 DevOps 工具链",
                "完善监控告警",
                "知识分享常态化",
                "定期满意度调研"
            ],
            3: [  # 优化期
                "复盘扩展过程",
                "优化组织架构",
                "沉淀最佳实践",
                "规划下一阶段"
            ]
        }

        base_actions = actions.get(phase_idx, [])

        # 根据团队规模添加特定建议
        if team_size >= 30 and phase_idx >= 1:
            base_actions.append("考虑引入 Engineering Manager")

        return base_actions

    def _calculate_risks(self):
        """计算扩展风险"""
        risks = []

        # 招聘风险
        hire_velocity = (self.target_size - self.current_size) / self.months
        if hire_velocity > 5:
            risks.append({
                'type': '招聘风险',
                'level': '高',
                'description': f'每月需招聘 {hire_velocity:.1f} 人，市场供给可能不足',
                'mitigation': '提前启动招聘，建立人才库，考虑外包过渡'
            })

        # 文化稀释风险
        expansion_ratio = self.target_size / self.current_size
        if expansion_ratio > 2:
            risks.append({
                'type': '文化稀释',
                'level': '高',
                'description': f'团队规模将扩大 {expansion_ratio:.1f} 倍，文化可能被稀释',
                'mitigation': '加强文化建设，创始人参与新人培训，建立核心价值观培训'
            })

        # 管理复杂度风险
        if self.target_size >= 30:
            risks.append({
                'type': '管理复杂度',
                'level': '中',
                'description': '团队规模超过 30 人，需要引入中层管理',
                'mitigation': '提前培养 Tech Lead，引入 Engineering Manager，小团队自治'
            })

        # 产出下降风险
        if expansion_ratio > 2.5:
            final_productivity = self.COMMUNICATION_OVERHEAD.get(50, 0.7)
            risks.append({
                'type': '产出下降',
                'level': '中',
                'description': f'扩展期人均产出可能下降 {(1-final_productivity)*100:.0f}%',
                'mitigation': '合理设定期望，聚焦长期效率，投资工具和自动化'
            })

        # 入职培训风险
        total_new = self.target_size - self.current_size
        if total_new > 20:
            risks.append({
                'type': '培训压力',
                'level': '中',
                'description': f'需培训 {total_new} 名新人，导师资源可能不足',
                'mitigation': '建立标准化培训材料，轮值导师制度，学习平台支持'
            })

        self.plan.risks = risks

    def _generate_recommendations(self):
        """生成建议"""
        recs = []

        # 基于规模的建议
        if self.target_size >= 50:
            recs.append("考虑按产品线或业务域划分独立团队")
            recs.append("引入工程效能团队，专注于工具和流程优化")

        if self.target_size >= 30:
            recs.append("建立清晰的职级体系和晋升通道")
            recs.append("实施技术委员会机制，统筹技术决策")

        # 基于扩展速度的建议
        monthly_hire = (self.target_size - self.current_size) / self.months
        if monthly_hire > 3:
            recs.append(f"招聘压力大({monthly_hire:.1f}人/月)，建议提前 2-3 个月启动招聘")
            recs.append("考虑与猎头合作，或启用内推奖励机制")

        # 通用建议
        recs.append("每两周回顾扩展进度，及时调整计划")
        recs.append("关注团队士气，定期一对一沟通")
        recs.append("文档先行：在快速扩展前完善技术文档")

        self.plan.recommendations = recs

    def _calculate_summary(self):
        """计算汇总信息"""
        total_hires = self.target_size - self.current_size
        avg_hire_per_month = total_hires / self.months

        # 计算平均产出率
        if self.plan.phases:
            avg_productivity = sum(p.productivity_factor for p in self.plan.phases) / len(self.plan.phases)
        else:
            avg_productivity = 1.0

        # 计算高峰期规模（考虑离职率）
        attrition_rate = 0.15  # 假设 15% 年离职率
        buffer = int(self.target_size * attrition_rate / 12 * self.months)

        self.plan.summary = {
            'current_size': self.current_size,
            'target_size': self.target_size,
            'total_new_hires': total_hires,
            'duration_months': self.months,
            'avg_hires_per_month': round(avg_hire_per_month, 1),
            'expansion_ratio': round(self.target_size / self.current_size, 2),
            'avg_productivity_factor': round(avg_productivity, 2),
            'recommended_peak_hiring': total_hires + buffer,
            'estimated_full_productivity_month': self.months + self.onboarding_months,
            'high_risk_count': len([r for r in self.plan.risks if r['level'] == '高']),
            'medium_risk_count': len([r for r in self.plan.risks if r['level'] == '中'])
        }

    def generate_text_report(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("团队扩展规划报告")
        lines.append("=" * 60)
        lines.append("")

        # 汇总
        s = self.plan.summary
        lines.append("【扩展概览】")
        lines.append(f"当前规模: {s['current_size']} 人")
        lines.append(f"目标规模: {s['target_size']} 人")
        lines.append(f"扩展周期: {s['duration_months']} 个月")
        lines.append(f"新增人数: {s['total_new_hires']} 人")
        lines.append(f"月均招聘: {s['avg_hires_per_month']} 人")
        lines.append(f"扩展倍数: {s['expansion_ratio']}x")
        lines.append(f"平均产出系数: {s['avg_productivity_factor']}")
        lines.append(f"预计满产时间: 第 {s['estimated_full_productivity_month']} 月")
        lines.append("")

        # 阶段计划
        lines.append("【阶段计划】")
        for phase in self.plan.phases:
            lines.append(f"\n{phase.name} (第 {phase.month} 月)")
            lines.append(f"  团队规模: {phase.team_size} 人")
            lines.append(f"  本阶段入职: {phase.new_hires} 人")
            lines.append(f"  产出系数: {phase.productivity_factor}")
            lines.append(f"  有效产出: {phase.effective_output}")
            lines.append(f"  关键行动:")
            for action in phase.key_actions:
                lines.append(f"    - {action}")

        # 风险评估
        lines.append("\n【风险评估】")
        for risk in self.plan.risks:
            lines.append(f"\n[{risk['level']}风险] {risk['type']}")
            lines.append(f"  描述: {risk['description']}")
            lines.append(f"  缓解措施: {risk['mitigation']}")

        # 建议
        lines.append("\n【建议】")
        for i, rec in enumerate(self.plan.recommendations, 1):
            lines.append(f"  {i}. {rec}")

        # 沟通成本曲线
        lines.append("\n【沟通成本曲线】")
        lines.append("团队规模 vs 沟通成本系数:")
        for size, factor in sorted(self.COMMUNICATION_OVERHEAD.items()):
            lines.append(f"  {size} 人: {factor*100:.0f}%")
        lines.append(f"\n当前 {self.current_size} 人 → 目标 {self.target_size} 人")
        start_factor = self._get_communication_factor(self.current_size)
        end_factor = self._get_communication_factor(self.target_size)
        lines.append(f"沟通成本系数: {start_factor*100:.0f}% → {end_factor*100:.0f}%")

        return '\n'.join(lines)

    def generate_json_report(self) -> str:
        """生成 JSON 报告"""
        return json.dumps({
            'summary': self.plan.summary,
            'phases': [
                {
                    'name': p.name,
                    'month': p.month,
                    'team_size': p.team_size,
                    'new_hires': p.new_hires,
                    'productivity_factor': p.productivity_factor,
                    'effective_output': p.effective_output,
                    'key_actions': p.key_actions
                }
                for p in self.plan.phases
            ],
            'risks': self.plan.risks,
            'recommendations': self.plan.recommendations
        }, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='计算团队扩展规划')
    parser.add_argument('--current', '-c', type=int, required=True,
                        help='当前团队规模')
    parser.add_argument('--target', '-t', type=int, required=True,
                        help='目标团队规模')
    parser.add_argument('--months', '-m', type=int, required=True,
                        help='扩展周期（月）')
    parser.add_argument('--current-productivity', type=float, default=100.0,
                        help='当前人均产出基准（默认100）')
    parser.add_argument('--onboarding-months', type=int, default=3,
                        help='新人达到满产所需月数（默认3）')
    parser.add_argument('--format', '-f', choices=['text', 'json'],
                        default='text', help='输出格式')
    parser.add_argument('--output', '-o', help='输出文件')

    args = parser.parse_args()

    # 验证输入
    if args.target <= args.current:
        print("错误: 目标规模必须大于当前规模")
        return

    if args.months < 3:
        print("警告: 建议扩展周期至少 3 个月")

    # 计算
    calculator = TeamScalingCalculator(
        args.current, args.target, args.months,
        args.current_productivity, args.onboarding_months
    )
    plan = calculator.calculate()

    # 生成报告
    if args.format == 'json':
        output = calculator.generate_json_report()
    else:
        output = calculator.generate_text_report()

    # 输出
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"报告已保存到: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
