#!/usr/bin/env python3
"""
Project Management Toolkit
项目管理实用工具：WBS编号生成、工期计算、风险矩阵
"""

import argparse
from datetime import datetime, timedelta
from typing import List, Dict
import json


def generate_wbs_code(level: int, parent_code: str = "", index: int = 1) -> str:
    """生成 WBS 编号"""
    if level == 1:
        return str(index)
    return f"{parent_code}.{index}"


def parse_wbs_hierarchy(codes: List[str]) -> Dict:
    """解析 WBS 层级结构"""
    tree = {}

    for code in sorted(codes, key=lambda x: [int(n) for n in x.split(".")]):
        parts = code.split(".")
        current = tree

        for i, part in enumerate(parts):
            prefix = ".".join(parts[:i+1])
            if prefix not in current:
                current[prefix] = {}
            current = current[prefix]

    return tree


def print_wbs_tree(tree: Dict, indent: int = 0):
    """打印 WBS 树"""
    for key in sorted(tree.keys(), key=lambda x: [int(n) for n in x.split(".")]):
        level = key.count(".") + 1
        prefix = "  " * (level - 1)
        print(f"{prefix}{key}")
        if tree[key]:
            print_wbs_tree(tree[key], indent + 1)


def calculate_critical_path(tasks: List[Dict]) -> List[str]:
    """
    简化版关键路径计算
    tasks: [{"id": str, "duration": int, "dependencies": [str]}]
    """
    # 计算最早开始/结束
    es = {}  # Early Start
    ef = {}  # Early Finish

    # 按依赖拓扑排序 (简化实现)
    completed = set()
    remaining = {t["id"] for t in tasks}

    while remaining:
        progress = False
        for task in tasks:
            if task["id"] in remaining:
                deps = set(task.get("dependencies", []))
                if deps <= completed:
                    # 可以计算
                    if deps:
                        es[task["id"]] = max(ef[d] for d in deps)
                    else:
                        es[task["id"]] = 0
                    ef[task["id"]] = es[task["id"]] + task["duration"]
                    completed.add(task["id"])
                    remaining.remove(task["id"])
                    progress = True

        if not progress and remaining:
            raise ValueError("存在循环依赖或无效依赖")

    # 计算最晚开始/结束 (逆向)
    project_duration = max(ef.values())
    ls = {}  # Late Start
    lf = {}  # Late Finish

    for task in reversed(tasks):
        task_id = task["id"]
        successors = [t for t in tasks if task_id in t.get("dependencies", [])]

        if not successors:
            lf[task_id] = project_duration
        else:
            lf[task_id] = min(ls[s["id"]] for s in successors)

        ls[task_id] = lf[task_id] - task["duration"]

    # 计算浮动时间
    float_times = {}
    for task in tasks:
        tid = task["id"]
        float_times[tid] = ls[tid] - es[tid]

    # 关键路径 = 浮动时间为0的任务
    critical_path = [t["id"] for t in tasks if float_times[t["id"]] == 0]

    return critical_path


def risk_matrix(probability: int, impact: int) -> Dict:
    """
    风险矩阵评估

    Args:
        probability: 概率 (1-5)
        impact: 影响 (1-5)

    Returns:
        风险评估结果
    """
    score = probability * impact

    if score >= 15:
        level = "高风险"
        color = "🔴"
        action = "立即采取应对措施"
    elif score >= 8:
        level = "中风险"
        color = "🟡"
        action = "制定应对计划"
    else:
        level = "低风险"
        color = "🟢"
        action = "定期监控"

    return {
        "score": score,
        "level": level,
        "color": color,
        "action": action
    }


def calculate_earned_value(
    bac: float,  # 预算 at Completion
    pv: float,   # Planned Value
    ev: float,   # Earned Value
    ac: float    # Actual Cost
) -> Dict:
    """
    挣值计算
    """
    # 偏差
    sv = ev - pv  # 进度偏差
    cv = ev - ac  # 成本偏差

    # 绩效指数
    spi = ev / pv if pv > 0 else 0  # 进度绩效
    cpi = ev / ac if ac > 0 else 0  # 成本绩效

    # 预测
    eac = bac / cpi if cpi > 0 else bac  # 完工估算
    etc = eac - ac  # 完工尚需
    vac = bac - eac  # 完工偏差

    return {
        "sv": sv,
        "cv": cv,
        "spi": spi,
        "cpi": cpi,
        "eac": eac,
        "etc": etc,
        "vac": vac,
        "interpretation": {
            "schedule": "超前" if spi > 1.05 else ("正常" if spi >= 0.95 else "滞后"),
            "cost": "节约" if cpi > 1.05 else ("正常" if cpi >= 0.95 else "超支")
        }
    }


def generate_gantt_data(tasks: List[Dict], start_date: str) -> List[Dict]:
    """生成甘特图数据"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    task_list = []

    for i, task in enumerate(tasks):
        task_start = start + timedelta(days=sum(t["duration"] for t in tasks[:i]))
        task_end = task_start + timedelta(days=task["duration"])

        task_list.append({
            "id": task["id"],
            "name": task.get("name", task["id"]),
            "start": task_start.strftime("%Y-%m-%d"),
            "end": task_end.strftime("%Y-%m-%d"),
            "duration": task["duration"],
            "progress": task.get("progress", 0)
        })

    return task_list


def main():
    parser = argparse.ArgumentParser(description="Project Management Toolkit")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # WBS 命令
    wbs_parser = subparsers.add_parser("wbs", help="WBS 工具")
    wbs_parser.add_argument("--example", action="store_true", help="显示示例 WBS")

    # 关键路径命令
    cp_parser = subparsers.add_parser("cp", help="关键路径计算")
    cp_parser.add_argument("--file", help="任务 JSON 文件路径")

    # 风险矩阵命令
    risk_parser = subparsers.add_parser("risk", help="风险评估")
    risk_parser.add_argument("--prob", type=int, required=True, help="概率 (1-5)")
    risk_parser.add_argument("--impact", type=int, required=True, help="影响 (1-5)")

    # 挣值命令
    ev_parser = subparsers.add_parser("ev", help="挣值计算")
    ev_parser.add_argument("--bac", type=float, required=True, help="总预算")
    ev_parser.add_argument("--pv", type=float, required=True, help="计划值")
    ev_parser.add_argument("--ev", type=float, required=True, help="挣值")
    ev_parser.add_argument("--ac", type=float, required=True, help="实际成本")

    args = parser.parse_args()

    if args.command == "wbs":
        if args.example:
            example_codes = ["1", "1.1", "1.2", "2", "2.1", "2.2", "2.2.1", "2.2.2", "3"]
            print("\n示例 WBS 结构:")
            print("=" * 40)
            tree = parse_wbs_hierarchy(example_codes)
            print_wbs_tree(tree)
            print()
        else:
            # 生成功能
            print("\nWBS 编号生成:")
            for i in range(1, 4):
                code = generate_wbs_code(1, index=i)
                print(f"  {code}: 阶段 {i}")
                for j in range(1, 3):
                    sub_code = generate_wbs_code(2, code, j)
                    print(f"    {sub_code}: 工作包 {j}")
            print()

    elif args.command == "cp":
        # 示例任务
        tasks = [
            {"id": "A", "duration": 3, "dependencies": []},
            {"id": "B", "duration": 4, "dependencies": ["A"]},
            {"id": "C", "duration": 2, "dependencies": ["A"]},
            {"id": "D", "duration": 5, "dependencies": ["B", "C"]},
        ]

        if args.file:
            with open(args.file) as f:
                tasks = json.load(f)

        try:
            critical = calculate_critical_path(tasks)
            print(f"\n关键路径: {' → '.join(critical)}\n")
        except Exception as e:
            print(f"错误: {e}")

    elif args.command == "risk":
        result = risk_matrix(args.prob, args.impact)
        print(f"\n风险评估结果:")
        print(f"  概率: {args.prob}/5")
        print(f"  影响: {args.impact}/5")
        print(f"  风险分: {result['score']}")
        print(f"  风险等级: {result['color']} {result['level']}")
        print(f"  建议行动: {result['action']}\n")

    elif args.command == "ev":
        result = calculate_earned_value(args.bac, args.pv, args.ev, args.ac)
        print(f"\n挣值分析结果:")
        print(f"  预算 (BAC): {args.bac:,.2f}")
        print(f"  计划值 (PV): {args.pv:,.2f}")
        print(f"  挣值 (EV): {args.ev:,.2f}")
        print(f"  实际成本 (AC): {args.ac:,.2f}")
        print()
        print(f"  进度偏差 (SV): {result['sv']:,.2f}")
        print(f"  成本偏差 (CV): {result['cv']:,.2f}")
        print(f"  进度绩效 (SPI): {result['spi']:.2f} ({result['interpretation']['schedule']})")
        print(f"  成本绩效 (CPI): {result['cpi']:.2f} ({result['interpretation']['cost']})")
        print()
        print(f"  完工估算 (EAC): {result['eac']:,.2f}")
        print(f"  完工尚需 (ETC): {result['etc']:,.2f}")
        print(f"  完工偏差 (VAC): {result['vac']:,.2f}\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
