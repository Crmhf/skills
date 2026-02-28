---
name: memory
description: 完整的 Agent 记忆系统，包含捕获层（自动提取）、回忆层（关键词搜索）、维护层（整合）。使用 SESSION-STATE.md 作为活跃任务上下文存储。
triggers:
  - 记忆
  - 记录
  - 回忆
  - 搜索记忆
  - 上下文管理
  - session state
  - 知识库
---

# 记忆系统

完整的 OpenClaw Agent 记忆系统，支持长期记忆和短期上下文管理。

---

## 核心能力

| 能力领域 | 具体技能 |
|---------|---------|
| 协议层 | 定义何时保存、如何组织 |
| 捕获层 | 自动从对话中提取关键事实 |
| 回忆层 | 关键词搜索、语义检索 |
| 维护层 | 定期整合、去重、归档 |

---

## 使用方法

### 捕获记忆

```bash
python scripts/capture.py "关键信息" --category tech --tags "python,async"
```

### 回忆记忆

```bash
python scripts/recall.py "关键词" --limit 5
```

### 整合维护

```bash
python scripts/consolidate.py --dry-run
```

---

## 记忆结构

### SESSION-STATE.md（短期记忆）

存储活跃任务上下文：
- 当前任务列表
- 待解决问题
- 最近决策
- 临时上下文

### 记忆日志（长期记忆）

按日期组织的记忆文件：
```
memory/
├── 2024-01-15.md
├── 2024-01-16.md
└── index.json
```

---

## 记忆格式

```markdown
## 2024-01-15 14:30 [技术决策]

**主题**: 选择 PostgreSQL 作为主数据库

**内容**: 经过评估，团队决定采用 PostgreSQL 15 替代 MySQL 5.7，
主要原因是 JSONB 支持和更好的全文检索能力。

**标签**: #数据库 #PostgreSQL #架构决策

**相关**: [[ADR-001]]
```

---

## 参考文档

- `references/RECENT_CONTEXT.md` - 最近上下文使用指南
- `references/SESSION-STATE.md` - 会话状态管理规范

---

## 最佳实践

1. **自动捕获**: 在关键对话节点自动调用 capture
2. **定期整合**: 每周运行 consolidate 清理重复记忆
3. **标签分类**: 使用一致的标签体系便于检索
4. **双向链接**: 相关记忆使用 [[链接]] 建立关联
