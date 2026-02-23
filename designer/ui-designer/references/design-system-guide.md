# 设计系统构建指南

## 目录
1. [设计Token规范](#1-设计token规范)
2. [色彩系统设计](#2-色彩系统设计)
3. [字体系统设计](#3-字体系统设计)
4. [间距系统设计](#4-间距系统设计)
5. [组件设计模式](#5-组件设计模式)

---

## 1. 设计Token规范

### Token 层级结构

```
Token 层级:
├── 原始值 (Primitive)
│   ├── color-red-500: #EF4444
│   ├── spacing-4: 4px
│   └── font-size-16: 16px
│
├── 语义层 (Semantic)
│   ├── color-danger: → color-red-500
│   ├── spacing-md: → spacing-16
│   └── text-body: → font-size-16
│
└── 组件层 (Component)
    ├── button-primary-bg: → color-primary-500
    ├── button-padding: → spacing-md
    └── button-text: → text-body
```

### Token 命名规范

| 类型 | 命名格式 | 示例 |
|-----|---------|------|
| 颜色 | `{color}-{name}-{scale}` | `color-blue-500` |
| 间距 | `spacing-{scale}` | `spacing-16` |
| 字号 | `font-size-{scale}` | `font-size-14` |
| 圆角 | `radius-{scale}` | `radius-lg` |
| 阴影 | `shadow-{scale}` | `shadow-md` |

---

## 2. 色彩系统设计

### 主色板

```
主色阶 (以蓝色为例):
├── 50:  #EEF5FF  (最浅，用于背景)
├── 100: #D6E8FF
├── 200: #A8D0FF
├── 300: #79B5FF
├── 400: #4A9AFF
├── 500: #2B7FFF  (主色)
├── 600: #1A6FEF  (悬停)
├── 700: #0D5FD9  (按下)
├── 800: #084DB5
└── 900: #043A8C  (最深)

功能色:
├── Success: #00C853 (成功)
├── Warning: #FFB300 (警告)
├── Error:   #FF1744 (错误)
└── Info:    #00B0FF (信息)
```

### 中性色阶

```
中性色 (Gray Scale):
├── 50:  #FAFAFA  (最浅背景)
├── 100: #F5F5F5
├── 200: #E5E5E5 (边框)
├── 300: #D4D4D4
├── 400: #A3A3A3 (禁用文字)
├── 500: #737373
├── 600: #525252 (次要文字)
├── 700: #404040
├── 800: #262626
└── 900: #171717 (最深文字)
```

---

## 3. 字体系统设计

### 字体家族

```
字体栈 (Font Stack):
├── 中文:
│   └── "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif
├── 英文:
│   └── -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
└── 代码:
    └── "SF Mono", Monaco, "Cascadia Code", monospace
```

### 字号规范

| 层级 | 用途 | 桌面端 | 移动端 | 字重 | 行高 |
|-----|------|-------|-------|------|------|
| H1 | 页面标题 | 32px | 24px | 600 | 1.3 |
| H2 | 区块标题 | 24px | 20px | 600 | 1.4 |
| H3 | 卡片标题 | 20px | 18px | 600 | 1.4 |
| H4 | 小标题 | 18px | 16px | 500 | 1.5 |
| Body | 正文 | 14px | 14px | 400 | 1.6 |
| Small | 辅助文字 | 12px | 12px | 400 | 1.5 |

---

## 4. 间距系统设计

### 8px 基准系统

```
间距阶梯:
├── 0:   0px    (无间距)
├── 1:   4px    (xs - 图标内边距)
├── 2:   8px    (sm - 紧凑间距)
├── 3:   12px
├── 4:   16px   (md - 默认间距)
├── 5:   20px
├── 6:   24px   (lg - 区块间距)
├── 8:   32px   (xl - 模块间距)
├── 10:  40px
├── 12:  48px   (2xl - 页面间距)
└── 16:  64px   (3xl)
```

### 布局网格

```
桌面端 (≥1280px):
├── 列数: 12列
├── 列宽: 60px
├── 间距: 24px (gutter)
└── 边距: 32px

平板 (768-1279px):
├── 列数: 8列
├── 间距: 24px
└── 边距: 24px

移动端 (<768px):
├── 列数: 4列
├── 间距: 16px
└── 边距: 16px
```

---

## 5. 组件设计模式

### 按钮规范

```
按钮变体:
├── Primary (主要)
│   ├── 背景: color-primary-500
│   ├── 文字: white
│   └── 悬停: color-primary-600
├── Secondary (次要)
│   ├── 背景: transparent
│   ├── 边框: 1px solid color-primary-500
│   └── 文字: color-primary-500
└── Text (文字)
    ├── 背景: transparent
    └── 文字: color-primary-500

按钮尺寸:
├── Small:   高 28px, 内边距 8px 12px, 字号 12px
├── Medium:  高 36px, 内边距 12px 20px, 字号 14px (默认)
└── Large:   高 44px, 内边距 16px 28px, 字号 16px

状态样式:
├── Hover:   背景加深
├── Active:  背景更深, scale(0.98)
├── Disabled: 透明度 0.5, cursor: not-allowed
└── Loading: 显示加载图标, 禁用点击
```

### 输入框规范

```
基础样式:
├── 高度: 36px
├── 内边距: 12px 16px
├── 边框: 1px solid gray-300
├── 圆角: 8px
└── 背景: white

状态样式:
├── Default: 边框 gray-300
├── Hover:   边框 gray-400
├── Focus:   边框 primary-500, 阴影 ring
├── Error:   边框 red-500, 背景 red-50
└── Disabled: 背景 gray-100, 文字 gray-400

输入框组合:
├── Label: 位于上方, 间距 8px, 字号 14px
├── Helper: 位于下方, 字号 12px, 颜色 gray-500
└── Error:  位于下方, 字号 12px, 颜色 red-500
```

### 卡片规范

```
卡片基础:
├── 背景: white
├── 圆角: 12px
├── 内边距: 24px
└── 阴影: shadow-sm

卡片变体:
├── Outlined: 边框 1px solid gray-200
├── Elevated: 阴影 shadow-md
└── Filled:   背景 gray-50

卡片结构:
┌─────────────────────┐
│ [Header] 标题       │ ← 可选, 可包含操作按钮
├─────────────────────┤
│ [Content] 内容区域   │ ← 主要信息
├─────────────────────┤
│ [Footer] 底部操作   │ ← 可选, 如确认/取消按钮
└─────────────────────┘
```

---

## 6. 响应式断点

```javascript
// Tailwind 风格断点
const breakpoints = {
  sm: '640px',   // 手机横屏
  md: '768px',   // 平板竖屏
  lg: '1024px',  // 平板横屏/小桌面
  xl: '1280px',  // 标准桌面
  '2xl': '1536px' // 大桌面
}
```

---

## 7. 暗黑模式映射

```
映射规则:
├── 背景色: 反转 (white ↔ gray-900)
├── 表面色: 对应降低 (gray-100 ↔ gray-800)
├── 文字色: 反转 (gray-900 ↔ gray-100)
└── 强调色: 提高亮度 (primary-500 → primary-400)

注意事项:
1. 阴影在暗黑模式下应更微妙
2. 半透明遮罩需调整透明度
3. 图片/插画需适配或提供暗黑版本
4. 边框颜色应比背景稍亮
```

---

## 8. Figma 文件组织

```
文件结构:
├── 📁 00 - Foundations (基础)
│   ├── 🎨 Color
│   ├── 🔤 Typography
│   ├── 📏 Spacing
│   └── ✨ Effects
│
├── 📁 01 - Components (组件)
│   ├── Buttons
│   ├── Inputs
│   ├── Cards
│   └── ...
│
├── 📁 02 - Patterns (模式)
│   ├── Forms
│   ├── Navigation
│   └── Data Display
│
└── 📁 03 - Templates (模板)
    ├── Page Layouts
    └── Examples
```

---

*文档版本: v1.0 | 最后更新: 2024-01*
