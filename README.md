# AI 角色技能库

本仓库包含专业领域的 AI 角色技能定义，采用结构化格式（SKILL.md），支持 AI 助手在不同场景下提供专业服务。

## 目录结构

```
skills/
├── architect/          # 架构师系列
├── company/            # 企业职能系列
├── data/               # 数据工程师系列
├── designer/           # 设计师系列
├── developer/          # 开发工程师系列
├── doc/                # 文档工程师系列
├── other/              # 其他专业角色
├── product/            # 产品经理系列
├── solution/           # 解决方案系列
├── teach/              # 教育类角色
├── tools/              # 工具技能集合
└── README.md           # 本文件
```

## 完成状态

### ✅ 全部完成 - 73个技能

所有技能文件已按照统一标准更新完成，每个技能包含：
- YAML frontmatter（name, description, triggers）
- 核心能力表格
- 5个标杆角色对话示例
- Tech Stack

| 分类 | 数量 | 状态 |
|------|------|------|
| architect | 7 | ✅ 全部完成 |
| company | 10 | ✅ 全部完成 |
| data | 8 | ✅ 全部完成 |
| designer | 7 | ✅ 全部完成 |
| developer | 8 | ✅ 全部完成 |
| doc | 5 | ✅ 全部完成 |
| other | 5 | ✅ 全部完成 |
| product | 11 | ✅ 全部完成 |
| solution | 6 | ✅ 全部完成 |
| teach | 6 | ✅ 全部完成 |

**总计: 73/73 技能已完成**

### 新增技能 - Agent Tools

| 分类 | 技能 | 说明 |
|-----|------|------|
| architect | `senior-architect` | 资深架构师 - 系统设计、架构决策、技术选型 |
| architect | `cto-advisor` | CTO 技术顾问 - 技术债务分析、团队扩展、DORA指标 |
| tools | `bing-search` | Bing 搜索引擎 - 无需 API Key |
| tools | `duckduckgo-search` | DuckDuckGo 隐私搜索 - 支持文本/新闻/图片/视频 |
| tools | `memory` | 记忆系统 - 捕获、回忆、维护 |
| tools | `csv-pipeline` | CSV 数据处理管道 - 清洗、转换、分析 |

## 分类说明

### 1. architect - 架构师系列
系统架构和技术架构相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `system-architect` | 系统架构师 - 企业级系统架构设计 |
| `cloud-architect` | 云架构师 - 云计算和基础设施架构 |
| `solution-architect` | 解决方案架构师 - 端到端解决方案设计 |
| `security-architect` | 安全架构师 - 安全架构和风险评估 |
| `backend-architect` | 后端架构师 - 服务端架构设计 |
| `data-architect` | 数据架构师 - 数据架构和治理 |
| `integration-architect` | 集成架构师 - 系统集成和API管理 |
| `senior-architect` | 资深架构师 - 系统设计、架构决策、技术选型、架构评审 |
| `cto-advisor` | CTO 技术顾问 - 技术债务分析、团队扩展规划、DORA指标、工程效能 |

### 2. company - 企业职能系列
企业运营和管理相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `product-manager` | 产品经理 - 产品全生命周期管理 |
| `project-manager` | 项目经理 - 项目规划与交付 |
| `scrum-master` | Scrum Master - 敏捷团队引导 |
| `operations-manager` | 运营经理 - 用户与业务运营 |
| `marketing-manager` | 市场营销经理 - 品牌营销与增长 |
| `sales-manager` | 销售经理 - 销售团队管理 |
| `hiring-manager` | 招聘经理 - 人才获取与管理 |
| `hr-specialist` | 人力资源专员 - HR全模块服务 |
| `ceo-assistant` | 高管助理 - 高管行政支持 |
| `legal-advisor` | 法律顾问 - 法律风险与合规 |

### 3. data - 数据工程师系列
数据相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `data-engineer` | 数据工程师 - ETL与数据管道 |
| `data-analyst` | 数据分析师 - 业务数据分析 |
| `data-scientist` | 数据科学家 - 算法与建模 |
| `ml-engineer` | 机器学习工程师 - ML工程化 |
| `bi-analyst` | 商业智能分析师 - BI与报表 |
| `database-admin` | 数据库管理员 - DBA |
| `data-warehouse` | 数据仓库架构师 - 数仓建设 |
| `big-data-engineer` | 大数据开发工程师 - 大数据平台 |

### 4. designer - 设计师系列
设计相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `ui-designer` | UI设计师 - 界面视觉设计 |
| `ux-designer` | UX设计师 - 用户体验设计 |
| `product-designer` | 产品设计师 - 全流程产品设计 |
| `graphic-designer` | 平面设计师 - 品牌与营销物料 |
| `interaction-designer` | 交互设计师 - 交互与动效设计 |
| `visual-designer` | 视觉设计师 - 视觉风格与美学 |
| `brand-designer` | 品牌设计师 - 品牌识别系统 |

### 5. developer - 开发工程师系列
软件开发相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `frontend-developer` | 前端开发工程师 - Web/移动端 |
| `backend-developer` | 后端开发工程师 - 服务端开发 |
| `mobile-developer` | 移动开发工程师 - iOS/Android |
| `game-developer` | 游戏开发工程师 - 游戏引擎开发 |
| `embedded-developer` | 嵌入式开发工程师 - 嵌入式系统 |
| `devops-developer` | DevOps工程师 - CI/CD与运维 |
| `fullstack-developer` | 全栈开发工程师 - 全栈应用开发 |
| `qa-developer` | 测试开发工程师 - 自动化测试 |

### 6. doc - 文档工程师系列
文档和知识管理相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `technical-writer` | 技术文档工程师 - 技术写作 |
| `api-documenter` | API文档工程师 - API文档与开发者体验 |
| `product-documenter` | 产品文档工程师 - 产品帮助文档 |
| `technical-translator` | 技术翻译专家 - 本地化与翻译 |
| `knowledge-manager` | 知识管理专家 - 知识库与知识运营 |

### 7. product - 产品经理系列
产品相关的专业角色（原有分类）。

| 子分类 | 说明 |
|--------|------|
| `product-plan` | 产品规划 |
| `product-design` | 产品设计 |
| `product-analysis` | 产品分析 |
| `product-strategy` | 产品战略 |
| `product-research` | 产品研究 |
| `product-operations` | 产品运营 |
| `product-growth` | 产品增长 |
| `product-analytics` | 产品数据分析 |
| `growth-hacking` | 增长黑客 |
| `requirements-analysis` | 需求分析 |
| `prompt-engineering` | 提示词工程 |

### 8. solution - 解决方案系列
解决方案和技术咨询相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `solution-engineer` | 解决方案工程师 - 技术方案设计 |
| `pre-sales-engineer` | 售前工程师 - 售前技术支持 |
| `implementation-engineer` | 实施工程师 - 项目交付实施 |
| `technical-consultant` | 技术顾问 - 技术咨询与规划 |
| `business-analyst` | 业务分析师 - 业务需求分析 |
| `requirements-analyst` | 需求分析师 - 需求工程 |

### 9. teach - 教育类角色
教育和培训相关的专业角色。

| 子分类 | 说明 |
|--------|------|
| `math-teacher` | 数学教师 - 数学与奥数教学 |
| `programming-teacher` | 编程教师 - 编程教育 |
| `language-teacher` | 语言教师 - 外语教学 |
| `science-teacher` | 科学教师 - 科学教育 |
| `ai-tutor` | AI辅导专家 - AI教育与培训 |
| `exam-coach` | 考试指导专家 - 考试备考辅导 |

### 10. other - 其他专业角色
其他难以归类但重要的专业角色。

| 子分类 | 说明 |
|--------|------|
| `ai-specialist` | AI应用专家 - AI工具应用 |
| `content-creator` | 内容创作者 - 多媒体内容创作 |
| `researcher` | 研究员 - 学术与行业研究 |
| `consultant` | 咨询顾问 - 管理与技术咨询 |
| `prompt-engineer` | 提示词工程师 - Prompt工程 |

### 11. tools - 工具技能集合
实用的工具技能，增强 Agent 能力。

| 子分类 | 说明 |
|--------|------|
| `bing-search` | Bing 搜索 - 网络搜索工具，无需 API Key |
| `duckduckgo-search` | DuckDuckGo 搜索 - 隐私友好的搜索引擎 |
| `memory` | 记忆系统 - 长期记忆管理，支持捕获/回忆/维护 |
| `csv-pipeline` | CSV 数据处理 - 数据清洗、转换、分析工具 |

## 文件格式

每个角色技能定义文件为 `SKILL.md`，采用 YAML Frontmatter + Markdown 内容的结构化格式：

```markdown
---
name: 角色英文标识
description: 角色描述（100字以内）
triggers:
  - 触发词1
  - 触发词2
  - ...
---

# 角色名称

角色简介

## 核心能力

| 能力领域 | 具体技能 |
|---------|---------|
| 领域1 | 技能1、技能2、技能3 |
| 领域2 | 技能4、技能5、技能6 |

## 标杆角色对话示例

### 示例1：场景标题

**用户:** 用户问题描述

**角色:** 专业回答内容，包含技术细节和最佳实践

### 示例2-5: ...

## Tech Stack

| 类别 | 推荐工具 |
|-----|---------|
| 类别1 | 工具1、工具2 |
| 类别2 | 工具3、工具4 |
```

### 文件夹结构

每个技能文件夹应包含：
```
skill-name/
├── SKILL.md              # 主要技能定义
├── references/           # 参考资料（必需）
│   ├── guide1.md
│   └── guide2.md
└── scripts/              # 自动化脚本（可选）
    └── utils.py
```

## 使用方式

1. 根据需求选择对应分类和子分类
2. 阅读 `SKILL.md` 了解角色能力边界
3. 在对话开始时引用角色定位，获取专业服务

## 贡献指南

如需添加新角色：

1. 选择合适的分类（或创建新分类）
2. 创建子文件夹（使用英文小写，单词间用连字符）
3. 编写 `SKILL.md` 文件，必须包含：
   - YAML frontmatter（name, description, triggers）
   - 核心能力表格
   - 至少3个标杆角色对话示例（用户问题+专家回答格式）
   - Tech Stack 推荐工具
4. 创建 `references/` 文件夹，存放相关参考文档
5. 更新本 README 的分类说明

### 标杆角色对话示例格式

```markdown
### 示例N：场景标题

**用户:** 具体业务问题描述

**角色名称:** 专业回答，包含：
- 分析思路
- 具体方案/步骤
- 技术细节（代码/配置/数据）
- 最佳实践建议
```

## 许可证

MIT License
