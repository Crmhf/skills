#!/usr/bin/env python3
"""
架构评审检查清单生成器
生成针对不同架构类型的评审检查清单
"""

import argparse
import json


# 评审检查项定义
CHECKLIST_ITEMS = {
    "microservices": {
        "name": "微服务架构评审",
        "items": [
            {"category": "服务划分", "checks": [
                "服务边界是否清晰，遵循单一职责原则？",
                "服务间依赖是否合理，避免循环依赖？",
                "数据所有权是否明确，避免跨服务直接访问数据库？",
            ]},
            {"category": "通信设计", "checks": [
                "同步/异步通信方式选择是否合理？",
                "是否设计了服务降级和熔断策略？",
                "API契约是否稳定，版本控制策略是否明确？",
            ]},
            {"category": "数据一致性", "checks": [
                "分布式事务方案是否明确(Saga/TCC/本地消息表)？",
                "最终一致性场景是否可接受？",
                "数据同步延迟对业务的影响是否评估？",
            ]},
            {"category": "可观测性", "checks": [
                "是否设计了统一的日志规范？",
                "链路追踪是否覆盖关键路径？",
                "业务指标和系统指标是否定义完整？",
            ]},
            {"category": "部署运维", "checks": [
                "服务发现机制是否设计？",
                "配置管理方案是否明确？",
                "故障隔离和恢复机制是否设计？",
            ]},
        ]
    },
    "high_availability": {
        "name": "高可用架构评审",
        "items": [
            {"category": "冗余设计", "checks": [
                "是否消除了单点故障？",
                "数据库是否有主从/多主架构？",
                "关键组件是否有多个实例？",
            ]},
            {"category": "故障转移", "checks": [
                "故障检测机制是否设计(健康检查/心跳)？",
                "自动切换策略是否明确？",
                "切换过程对业务的影响是否评估？",
            ]},
            {"category": "容灾设计", "checks": [
                "RPO/RTO指标是否明确？",
                "数据备份策略是否设计(全量/增量)？",
                "异地容灾方案是否必要？",
            ]},
            {"category": "限流降级", "checks": [
                "是否设计了多级限流策略？",
                "降级预案是否准备？",
                "熔断策略参数是否合理？",
            ]},
        ]
    },
    "distributed_systems": {
        "name": "分布式系统评审",
        "items": [
            {"category": "一致性设计", "checks": [
                "CAP定理取舍是否明确？",
                "一致性模型选择是否合理(强一致/最终一致)？",
                "分布式事务方案是否设计？",
            ]},
            {"category": "分区容错", "checks": [
                "网络分区场景是否考虑？",
                "脑裂问题是否有解决方案？",
                "分区恢复后数据一致性如何处理？",
            ]},
            {"category": "性能设计", "checks": [
                "数据分片策略是否设计？",
                "读写分离是否必要？",
                "缓存一致性如何保证？",
            ]},
        ]
    },
    "general": {
        "name": "通用架构评审",
        "items": [
            {"category": "功能性", "checks": [
                "是否满足所有业务需求？",
                "扩展性是否满足未来增长？",
                "安全性设计是否完整？",
            ]},
            {"category": "非功能性", "checks": [
                "性能指标(QPS/延迟)是否满足？",
                "可用性指标(SLA)是否明确？",
                "资源利用率是否合理？",
            ]},
            {"category": "可维护性", "checks": [
                "代码复杂度是否可控？",
                "测试覆盖是否充分？",
                "文档是否完整？",
            ]},
        ]
    }
}


def generate_checklist(arch_type: str, format_output: str = "markdown") -> str:
    """生成架构评审检查清单"""

    if arch_type not in CHECKLIST_ITEMS:
        available = ", ".join(CHECKLIST_ITEMS.keys())
        raise ValueError(f"未知架构类型: {arch_type}. 可用类型: {available}")

    config = CHECKLIST_ITEMS[arch_type]

    if format_output == "json":
        return json.dumps(config, ensure_ascii=False, indent=2)

    # Markdown format
    lines = [
        f"# {config['name']}检查清单",
        "",
        "使用此清单进行架构评审，确保关键设计点已被考虑。",
        "",
    ]

    for item in config["items"]:
        lines.append(f"## {item['category']}")
        lines.append("")
        for i, check in enumerate(item["checks"], 1):
            lines.append(f"- [ ] {i}. {check}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 评审结论",
        "",
        "| 检查项 | 通过 | 不通过 | 备注 |",
        "|--------|------|--------|------|",
    ])

    for item in config["items"]:
        for check in item["checks"]:
            short_check = check[:30] + "..." if len(check) > 30 else check
            lines.append(f"| {short_check} | ☐ | ☐ | |")

    lines.append("")
    lines.append("**评审意见:**")
    lines.append("")
    lines.append("**通过条件:** 所有关键检查项必须通过，非关键项可协商处理。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="生成架构评审检查清单",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python architecture_review_checklist.py --type microservices
  python architecture_review_checklist.py --type high_availability --format json
        """
    )

    parser.add_argument(
        "--type", "-t",
        choices=list(CHECKLIST_ITEMS.keys()),
        default="general",
        help="架构类型 (默认: general)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式 (默认: markdown)"
    )

    parser.add_argument(
        "--output", "-o",
        help="输出文件路径 (默认: 输出到stdout)"
    )

    args = parser.parse_args()

    try:
        result = generate_checklist(args.type, args.format)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"检查清单已生成: {args.output}")
        else:
            print(result)

    except ValueError as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
