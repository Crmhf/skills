# 记忆系统

完整的 OpenClaw Agent 记忆系统。

## 功能

- **捕获 (Capture)**: 从对话中提取关键信息
- **回忆 (Recall)**: 基于关键词检索历史记忆
- **整合 (Consolidate)**: 定期维护记忆文件

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```python
# 捕获记忆
from scripts.capture import capture_memory
capture_memory("重要技术决策", category="tech", tags=["架构", "数据库"])

# 回忆记忆
from scripts.recall import recall_memories
results = recall_memories("数据库")

# 整合维护
from scripts.consolidate import consolidate_memories
consolidate_memories()
```

## 目录结构

```
memory/
├── SKILL.md
├── README.md
├── _meta.json
├── references/
│   ├── RECENT_CONTEXT.md
│   └── SESSION-STATE.md
└── scripts/
    ├── capture.py
    ├── recall.py
    └── consolidate.py
```
