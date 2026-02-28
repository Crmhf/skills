---
name: bing-search
description: 使用 Bing 搜索引擎进行网络搜索，无需 API Key。支持获取搜索结果标题、URL 和摘要信息。
triggers:
  - bing搜索
  - 必应搜索
  - 网页搜索
  - 搜索工具
  - bing search
---

# Bing 搜索

使用 Bing 搜索引擎进行网络搜索，获取相关网页信息。

---

## 核心能力

| 能力 | 说明 |
|-----|------|
| 网页搜索 | 搜索关键词相关的网页 |
| 结果提取 | 获取标题、URL、摘要信息 |
| 无需 API Key | 直接使用，无需申请密钥 |

---

## 使用方法

### 命令行

```bash
python scripts/search.py "Python 教程" --limit 5
```

### Python 调用

```python
from scripts.search import search_bing

results = search_bing("Python 教程", limit=5)
for r in results:
    print(f"{r['title']}: {r['url']}")
```

---

## 输出格式

```json
[
  {
    "title": "页面标题",
    "url": "https://example.com/page",
    "snippet": "页面摘要..."
  }
]
```

---

## 注意事项

- 搜索结果可能受地区限制
- 频繁请求可能被限制，请合理控制调用频率
- 仅供个人学习研究使用
