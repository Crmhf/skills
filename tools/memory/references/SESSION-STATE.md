# 会话状态管理规范

SESSION-STATE.md 的结构和使用规范。

---

## 文件位置

```
workspace/
└── .claw/
    └── SESSION-STATE.md    # 活跃任务上下文
```

---

## 结构模板

```markdown
# Session State

## 元数据
- Created: 2024-01-15 10:00
- Updated: 2024-01-15 14:30
- Status: active

## 当前任务栈

### 任务1: [任务名称]
- 状态: in_progress / blocked / completed
- 优先级: P0 / P1 / P2
- 开始时间: 2024-01-15 10:00
- 上下文: [关键信息摘要]

### 任务2: [任务名称]
...

## 待办事项
- [ ] 待办1
- [ ] 待办2

## 关键决策记录
| 时间 | 决策 | 原因 |
|-----|------|------|
| 10:30 | 使用 PostgreSQL | JSON支持 |

## 环境信息
- 当前目录: /path/to/project
- 相关文件: [文件1, 文件2]

## 待确认问题
- [ ] 问题1: 需要用户确认的事项
```

---

## 状态流转

```
active → suspended → resumed → completed
   ↓
archived (超过30天)
```

---

## 清理策略

- **自动清理**: 已完成的任务保留7天后归档
- **手动清理**: 使用 consolidate 脚本定期整理
- **备份**: 归档到 memory/archive/ 目录
