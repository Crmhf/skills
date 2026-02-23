#!/usr/bin/env python3
"""
Prompt Optimizer - 提示词优化工具
帮助用户改进提示词，应用CO-STAR等框架
"""

import argparse
from typing import Dict, List


def analyze_prompt(prompt: str) -> Dict:
    """分析提示词的完整性和质量"""
    analysis = {
        "length": len(prompt),
        "has_context": any(kw in prompt.lower() for kw in ["背景", "context", "作为"]),
        "has_objective": any(kw in prompt.lower() for kw in ["目标", "请", "帮我", "需要"]),
        "has_format": any(kw in prompt.lower() for kw in ["格式", "json", "markdown", "表格"]),
        "score": 0,
        "suggestions": []
    }

    # 评分
    score = 50
    if analysis["has_context"]:
        score += 15
    else:
        analysis["suggestions"].append("建议添加背景信息（Context）")

    if analysis["has_objective"]:
        score += 20
    else:
        analysis["suggestions"].append("建议明确任务目标（Objective）")

    if analysis["has_format"]:
        score += 15
    else:
        analysis["suggestions"].append("建议指定输出格式（Response Format）")

    analysis["score"] = min(score, 100)
    return analysis


def apply_costar_framework(
    context: str = "",
    objective: str = "",
    style: str = "",
    tone: str = "",
    audience: str = "",
    response_format: str = ""
) -> str:
    """应用CO-STAR框架生成提示词"""
    parts = []

    if context:
        parts.append(f"【背景】\n{context}")
    if objective:
        parts.append(f"【目标】\n{objective}")
    if style:
        parts.append(f"【风格】\n{style}")
    if tone:
        parts.append(f"【语气】\n{tone}")
    if audience:
        parts.append(f"【受众】\n{audience}")
    if response_format:
        parts.append(f"【输出格式】\n{response_format}")

    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Prompt Optimizer")
    parser.add_argument("--analyze", "-a", help="分析现有提示词")
    parser.add_argument("--costar", "-c", action="store_true", help="使用CO-STAR框架")

    args = parser.parse_args()

    if args.analyze:
        result = analyze_prompt(args.analyze)
        print(f"\n提示词分析结果:")
        print(f"长度: {result['length']} 字符")
        print(f"质量评分: {result['score']}/100")
        print(f"\n改进建议:")
        for suggestion in result["suggestions"]:
            print(f"  • {suggestion}")

    elif args.costar:
        print("\n请按提示输入各部分内容（直接回车跳过）:")
        context = input("背景 (Context): ")
        objective = input("目标 (Objective): ")
        style = input("风格 (Style): ")
        tone = input("语气 (Tone): ")
        audience = input("受众 (Audience): ")
        response_format = input("输出格式 (Response): ")

        optimized = apply_costar_framework(
            context, objective, style, tone, audience, response_format
        )
        print(f"\n{'='*50}")
        print("优化后的提示词:")
        print(f"{'='*50}\n")
        print(optimized)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
