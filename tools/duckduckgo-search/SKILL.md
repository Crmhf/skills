---
name: duckduckgo-search
description: 基于 DuckDuckGo 的隐私友好型搜索，无需 API Key。支持文本搜索、新闻搜索、图片搜索、视频搜索。
triggers:
  - duckduckgo搜索
  - duck搜索
  - 隐私搜索
  - ddg搜索
  - 网页搜索
---

# DuckDuckGo 搜索

基于 DuckDuckGo 的隐私友好型搜索引擎，不追踪用户搜索历史。

---

## 核心能力

| 能力 | 说明 |
|-----|------|
| 文本搜索 | 常规网页搜索 |
| 新闻搜索 | 获取最新新闻资讯 |
| 图片搜索 | 搜索相关图片 |
| 视频搜索 | 搜索视频内容 |
| 隐私保护 | 不追踪用户、不记录历史 |

---

## 使用方法

### Python 调用

```python
from duckduckgo_search import DDGS

# 文本搜索
with DDGS() as ddgs:
    results = ddgs.text("Python 教程", max_results=5)
    for r in results:
        print(r["title"], r["href"])

# 新闻搜索
with DDGS() as ddgs:
    results = ddgs.news("AI 人工智能", max_results=5)

# 图片搜索
with DDGS() as ddgs:
    results = ddgs.images("风景壁纸", max_results=5)
```

---

## 安装依赖

```bash
pip install duckduckgo-search
```

---

## 输出格式

```python
# 文本搜索结果
{
    "title": "页面标题",
    "href": "https://example.com",
    "body": "页面摘要"
}

# 新闻搜索结果
{
    "title": "新闻标题",
    "href": "https://news.example.com/article",
    "body": "新闻摘要",
    "date": "2024-01-15"
}

# 图片搜索结果
{
    "title": "图片标题",
    "image": "https://example.com/image.jpg",
    "thumbnail": "https://example.com/thumb.jpg",
    "url": "https://example.com/page",
    "height": 1080,
    "width": 1920,
    "source": "来源网站"
}
```

---

## 高级用法

```python
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    # 指定地区
    results = ddgs.text("Python", region="zh-cn")

    # 指定时间范围
    results = ddgs.text("新闻", timelimit="d")  # d=天, w=周, m=月, y=年

    # 安全搜索
    results = ddgs.text("关键词", safesearch="moderate")  # on, moderate, off
```

---

## 注意事项

- 免费使用，无需 API Key
- 有速率限制，请勿频繁请求
- 仅供个人学习研究使用
