#!/usr/bin/env python3
"""
UX Research Calculator
计算样本量、置信区间、统计显著性
"""

import math
import argparse
from typing import Tuple


def sample_size_for_proportion(
    margin_of_error: float = 0.05,
    confidence_level: float = 0.95,
    population_proportion: float = 0.5,
    population_size: int = None
) -> int:
    """
    计算比例估计所需的样本量

    Args:
        margin_of_error: 允许的误差范围 (默认 5%)
        confidence_level: 置信水平 (默认 95%)
        population_proportion: 预期比例 (默认 0.5，最保守估计)
        population_size: 总体大小 (None 表示无限总体)

    Returns:
        所需样本量
    """
    # Z值对应置信水平
    z_scores = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576
    }
    z = z_scores.get(confidence_level, 1.96)

    # 初始样本量计算
    n = (z ** 2 * population_proportion * (1 - population_proportion)) / (margin_of_error ** 2)

    # 有限总体校正
    if population_size and population_size > 0:
        n = (n * population_size) / (n + population_size - 1)

    return math.ceil(n)


def confidence_interval(
    n: int,
    successes: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    计算比例的置信区间

    Args:
        n: 样本量
        successes: 成功次数
        confidence_level: 置信水平

    Returns:
        (下限, 上限)
    """
    p = successes / n
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_scores.get(confidence_level, 1.96)

    se = math.sqrt(p * (1 - p) / n)
    margin = z * se

    return (max(0, p - margin), min(1, p + margin))


def ab_test_significance(
    control_visitors: int,
    control_conversions: int,
    treatment_visitors: int,
    treatment_conversions: int
) -> dict:
    """
    A/B 测试显著性检验

    Returns:
        包含p值、提升率、建议的字典
    """
    p1 = control_conversions / control_visitors
    p2 = treatment_conversions / treatment_visitors

    # 合并比例
    p_pooled = (control_conversions + treatment_conversions) / (control_visitors + treatment_visitors)

    # 标准误
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/control_visitors + 1/treatment_visitors))

    # Z分数
    z = (p2 - p1) / se if se > 0 else 0

    # 简化的p值计算 (双尾)
    # 实际应用中应使用 scipy.stats
    p_value = 2 * (1 - normal_cdf(abs(z)))

    # 提升率
    lift = ((p2 - p1) / p1 * 100) if p1 > 0 else 0

    # 建议
    if p_value < 0.05:
        recommendation = "结果显著，建议采用新方案" if lift > 0 else "新方案显著更差，保持原方案"
    elif p_value < 0.1:
        recommendation = "趋势明显，建议增加样本量继续测试"
    else:
        recommendation = "结果不显著，建议继续测试或接受无差异"

    return {
        "control_rate": f"{p1:.2%}",
        "treatment_rate": f"{p2:.2%}",
        "lift": f"{lift:+.2f}%",
        "z_score": round(z, 4),
        "p_value": f"{p_value:.4f}",
        "significant": p_value < 0.05,
        "recommendation": recommendation
    }


def normal_cdf(x: float) -> float:
    """标准正态分布累积分布函数 (近似)"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def sus_score_interpretation(score: float) -> str:
    """解释 SUS 分数"""
    if score >= 85:
        return "优秀 (Excellent)"
    elif score >= 70:
        return "良好 (Good)"
    elif score >= 50:
        return "一般 (OK)"
    else:
        return "较差 (Poor)"


def nps_interpretation(score: float) -> str:
    """解释 NPS 分数"""
    if score >= 50:
        return "优秀"
    elif score >= 30:
        return "良好"
    elif score >= 0:
        return "一般"
    else:
        return "需改进"


def main():
    parser = argparse.ArgumentParser(description="UX Research Calculator")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 样本量计算
    sample_parser = subparsers.add_parser("sample", help="计算所需样本量")
    sample_parser.add_argument("--moe", type=float, default=0.05, help="允许误差 (默认0.05)")
    sample_parser.add_argument("--confidence", type=float, default=0.95, help="置信水平 (默认0.95)")
    sample_parser.add_argument("--population", type=int, help="总体大小 (可选)")

    # 置信区间
    ci_parser = subparsers.add_parser("ci", help="计算置信区间")
    ci_parser.add_argument("n", type=int, help="样本量")
    ci_parser.add_argument("successes", type=int, help="成功次数")
    ci_parser.add_argument("--confidence", type=float, default=0.95, help="置信水平")

    # A/B测试
    ab_parser = subparsers.add_parser("ab", help="A/B测试显著性")
    ab_parser.add_argument("--control-n", type=int, required=True, help="对照组样本量")
    ab_parser.add_argument("--control-conv", type=int, required=True, help="对照组转化数")
    ab_parser.add_argument("--treatment-n", type=int, required=True, help="实验组样本量")
    ab_parser.add_argument("--treatment-conv", type=int, required=True, help="实验组转化数")

    # SUS评分
    sus_parser = subparsers.add_parser("sus", help="解读SUS分数")
    sus_parser.add_argument("score", type=float, help="SUS分数 (0-100)")

    # NPS评分
    nps_parser = subparsers.add_parser("nps", help="解读NPS分数")
    nps_parser.add_argument("score", type=float, help="NPS分数 (-100到100)")

    args = parser.parse_args()

    if args.command == "sample":
        n = sample_size_for_proportion(
            margin_of_error=args.moe,
            confidence_level=args.confidence,
            population_size=args.population
        )
        print(f"\n样本量计算结果:")
        print(f"- 允许误差: {args.moe:.1%}")
        print(f"- 置信水平: {args.confidence:.0%}")
        if args.population:
            print(f"- 总体大小: {args.population:,}")
        print(f"\n✓ 建议样本量: {n} 人\n")

    elif args.command == "ci":
        lower, upper = confidence_interval(args.n, args.successes, args.confidence)
        p = args.successes / args.n
        print(f"\n置信区间计算:")
        print(f"- 样本量: {args.n}")
        print(f"- 成功数: {args.successes}")
        print(f"- 成功率: {p:.2%}")
        print(f"- 置信水平: {args.confidence:.0%}")
        print(f"\n✓ 置信区间: [{lower:.2%}, {upper:.2%}]\n")

    elif args.command == "ab":
        result = ab_test_significance(
            args.control_n, args.control_conv,
            args.treatment_n, args.treatment_conv
        )
        print(f"\nA/B 测试结果:")
        print(f"- 对照组转化率: {result['control_rate']}")
        print(f"- 实验组转化率: {result['treatment_rate']}")
        print(f"- 相对提升: {result['lift']}")
        print(f"- P值: {result['p_value']}")
        print(f"- 统计显著: {'是 ✓' if result['significant'] else '否 ✗'}")
        print(f"\n💡 建议: {result['recommendation']}\n")

    elif args.command == "sus":
        interpretation = sus_score_interpretation(args.score)
        print(f"\nSUS 分数解读:")
        print(f"- 得分: {args.score:.1f}")
        print(f"- 评级: {interpretation}\n")

    elif args.command == "nps":
        interpretation = nps_interpretation(args.score)
        print(f"\nNPS 分数解读:")
        print(f"- 得分: {args.score:.1f}")
        print(f"- 评级: {interpretation}\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
