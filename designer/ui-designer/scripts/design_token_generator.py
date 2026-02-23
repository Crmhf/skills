#!/usr/bin/env python3
"""
Design Token Generator
生成设计Token JSON / CSS / SCSS 文件
"""

import json
import argparse
from typing import Dict, Any

# 基础设计系统配置
DEFAULT_CONFIG = {
    "colors": {
        "primary": {
            "50": "#E6F0FF",
            "100": "#B3D1FF",
            "200": "#80B3FF",
            "300": "#4D94FF",
            "400": "#1A75FF",
            "500": "#2B7FFF",
            "600": "#1A6FEF",
            "700": "#0D5FD9",
            "800": "#084DB5",
            "900": "#043A8C"
        },
        "neutral": {
            "white": "#FFFFFF",
            "50": "#FAFAFA",
            "100": "#F5F5F5",
            "200": "#E5E5E5",
            "300": "#D4D4D4",
            "400": "#A3A3A3",
            "500": "#737373",
            "600": "#525252",
            "700": "#404040",
            "800": "#262626",
            "900": "#171717"
        },
        "semantic": {
            "success": "#00C853",
            "warning": "#FFB300",
            "error": "#FF1744",
            "info": "#00B0FF"
        }
    },
    "spacing": {
        "0": "0px",
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "8": "32px",
        "10": "40px",
        "12": "48px",
        "16": "64px",
        "20": "80px"
    },
    "fontSizes": {
        "xs": "12px",
        "sm": "14px",
        "base": "16px",
        "lg": "18px",
        "xl": "20px",
        "2xl": "24px",
        "3xl": "32px"
    },
    "borderRadius": {
        "none": "0px",
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "full": "9999px"
    },
    "shadows": {
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
        "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
    }
}


def to_css_variables(tokens: Dict[str, Any], prefix: str = "--") -> str:
    """转换为 CSS 变量"""
    css_lines = [":root {"]

    def flatten(obj: Dict, parent_key: str = ""):
        for key, value in obj.items():
            new_key = f"{parent_key}-{key}" if parent_key else key
            if isinstance(value, dict):
                flatten(value, new_key)
            else:
                css_lines.append(f"  {prefix}{new_key}: {value};")

    flatten(tokens)
    css_lines.append("}")
    return "\n".join(css_lines)


def to_scss_variables(tokens: Dict[str, Any]) -> str:
    """转换为 SCSS 变量"""
    scss_lines = []

    def flatten(obj: Dict, parent_key: str = ""):
        for key, value in obj.items():
            new_key = f"{parent_key}-{key}" if parent_key else key
            if isinstance(value, dict):
                flatten(value, new_key)
            else:
                scss_lines.append(f"${new_key}: {value};")

    flatten(tokens)
    return "\n".join(scss_lines)


def generate_contrast_matrix(tokens: Dict) -> str:
    """生成色彩对比度矩阵"""
    import colorsys

    def hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def luminance(rgb: tuple) -> float:
        def channel(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = rgb
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

    def contrast_ratio(color1: str, color2: str) -> float:
        l1 = luminance(hex_to_rgb(color1))
        l2 = luminance(hex_to_rgb(color2))
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    colors = tokens.get("colors", {})
    all_colors = {}

    # 收集所有颜色
    for category, values in colors.items():
        if isinstance(values, dict):
            for name, value in values.items():
                if isinstance(value, str) and value.startswith("#"):
                    all_colors[f"{category}-{name}"] = value

    # 生成矩阵
    matrix = ["Color Contrast Matrix (WCAG 2.1):"]
    matrix.append("=" * 60)

    bg_colors = [c for c in all_colors if "neutral" in c or c.startswith("primary")]
    text_colors = ["neutral-900", "neutral-600", "neutral-400", "white"]

    for bg_name in bg_colors[:6]:
        bg_value = all_colors[bg_name]
        matrix.append(f"\nBackground: {bg_name} ({bg_value})")
        for text_name in text_colors:
            if text_name in all_colors:
                text_value = all_colors[text_name]
                ratio = contrast_ratio(bg_value, text_value)
                level = "✓ AAA" if ratio >= 7 else ("✓ AA" if ratio >= 4.5 else "✗ Fail")
                matrix.append(f"  {text_name}: {ratio:.2f} {level}")

    return "\n".join(matrix)


def main():
    parser = argparse.ArgumentParser(description="Design Token Generator")
    parser.add_argument("--format", choices=["json", "css", "scss", "all"], default="all")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--contrast", action="store_true", help="Generate contrast matrix")

    args = parser.parse_args()

    output_dir = args.output or "."

    if args.format in ("json", "all"):
        json_path = f"{output_dir}/tokens.json"
        with open(json_path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"✓ Generated: {json_path}")

    if args.format in ("css", "all"):
        css_path = f"{output_dir}/tokens.css"
        with open(css_path, "w") as f:
            f.write(to_css_variables(DEFAULT_CONFIG))
        print(f"✓ Generated: {css_path}")

    if args.format in ("scss", "all"):
        scss_path = f"{output_dir}/tokens.scss"
        with open(scss_path, "w") as f:
            f.write(to_scss_variables(DEFAULT_CONFIG))
        print(f"✓ Generated: {scss_path}")

    if args.contrast:
        contrast = generate_contrast_matrix(DEFAULT_CONFIG)
        print("\n" + contrast)


if __name__ == "__main__":
    main()
