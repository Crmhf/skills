---
name: csv-pipeline
description: 处理 CSV、TSV、JSON 数据文件的完整流程。包含标准命令行工具（head、awk、sort）和 Python 操作，支持过滤、转换、分组聚合、连接数据集、去重、数据清洗和 Markdown 报告生成。
triggers:
  - CSV处理
  - 数据处理
  - 数据清洗
  - 数据转换
  - TSV处理
  - JSON转换
  - 数据管道
---

# CSV 数据处理管道

处理 CSV、TSV、JSON 数据文件的完整流程工具集。

---

## 核心能力

| 能力 | 说明 |
|-----|------|
| 快速浏览 | 使用 head、tail、wc 快速了解数据结构 |
| 数据过滤 | 使用 awk、grep 筛选数据 |
| 数据转换 | CSV/TSV/JSON 互转 |
| 分组聚合 | 按列分组统计 |
| 数据连接 | 多表关联操作 |
| 数据去重 | 基于关键列去重 |
| 数据清洗 | 格式标准化、空值处理 |
| 报告生成 | 生成 Markdown 数据报告 |

---

## 快速参考

### 命令行工具速查

```bash
# 查看数据
head -n 5 data.csv
tail -n 10 data.csv
wc -l data.csv

# 过滤数据
awk -F',' '$3 > 100' data.csv          # 第3列大于100
grep "keyword" data.csv                 # 包含关键词
awk -F',' 'NR>1 && $2=="active"' data.csv  # 第2列等于active，跳过标题

# 排序
sort -t',' -k3 -n data.csv              # 按第3列数值排序
sort -t',' -k2 data.csv                 # 按第2列字母排序

# 去重
awk -F',' '!seen[$1]++' data.csv        # 按第1列去重

# 统计
awk -F',' '{sum+=$3} END {print sum}' data.csv  # 求和
awk -F',' '{count[$2]++} END {for(k in count) print k, count[k]}' data.csv  # 分组计数
```

### Python 处理

```python
import pandas as pd

# 读取数据
df = pd.read_csv('data.csv')

# 基础操作
df.head()                               # 前5行
df.describe()                           # 统计摘要
df['column'].value_counts()             # 值计数

# 过滤
df[df['amount'] > 100]
df[df['status'] == 'active']

# 分组聚合
df.groupby('category')['amount'].sum()
df.groupby('category').agg({'amount': 'sum', 'count': 'count'})

# 去重
df.drop_duplicates(subset=['id'])

# 合并
df1.merge(df2, on='id', how='left')

# 导出
df.to_csv('output.csv', index=False)
df.to_json('output.json', orient='records')
```

---

## 数据清洗模式

### 常见清洗操作

| 问题 | 解决方案 |
|-----|---------|
| 空值处理 | `df.fillna(0)` 或 `df.dropna()` |
| 格式转换 | `pd.to_datetime(df['date'])` |
| 字符串清理 | `df['name'].str.strip().str.lower()` |
| 类型转换 | `df['amount'].astype(float)` |
| 异常值检测 | 箱线图法、3σ原则 |

### 清洗流程模板

```python
import pandas as pd
import numpy as np

def clean_data(df):
    # 1. 移除完全重复行
    df = df.drop_duplicates()

    # 2. 处理空值
    df = df.fillna({'numeric_col': 0, 'string_col': 'unknown'})

    # 3. 类型转换
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

    # 4. 字符串清理
    df['name'] = df['name'].str.strip().str.title()

    # 5. 异常值处理
    Q1 = df['amount'].quantile(0.25)
    Q3 = df['amount'].quantile(0.75)
    IQR = Q3 - Q1
    df = df[~((df['amount'] < (Q1 - 1.5 * IQR)) | (df['amount'] > (Q3 + 1.5 * IQR)))]

    return df
```

---

## 报告生成

### Markdown 报告模板

```python
def generate_report(df, title="数据分析报告"):
    report = f"""# {title}

## 数据概览

- **总行数**: {len(df)}
- **总列数**: {len(df.columns)}
- **日期**: {pd.Timestamp.now().strftime('%Y-%m-%d')}

## 列统计

| 列名 | 类型 | 非空值 | 空值 | 唯一值 |
|-----|------|--------|------|--------|
"""

    for col in df.columns:
        report += f"| {col} | {df[col].dtype} | {df[col].count()} | {df[col].isnull().sum()} | {df[col].nunique()} |\n"

    report += "\n## 数值列统计\n\n"
    report += df.describe().to_markdown()

    return report
```

---

## 使用场景示例

### 场景1: 日志分析

```bash
# 提取错误日志并统计
awk '/ERROR/ {print $1, $2}' app.log | sort | uniq -c | sort -rn
```

### 场景2: 销售数据聚合

```python
# 按月统计销售额
df['month'] = df['date'].dt.to_period('M')
monthly_sales = df.groupby('month')['amount'].sum()
```

### 场景3: 数据合并

```python
# 合并订单和客户信息
result = orders.merge(customers, on='customer_id', how='left')
result = result.merge(products, on='product_id', how='left')
```

---

## 工具对比

| 任务 | 命令行 | Python | 推荐 |
|-----|--------|--------|------|
| 快速查看 | ✅ | ⚠️ | 命令行 |
| 简单过滤 | ✅ | ✅ | 命令行 |
| 复杂转换 | ⚠️ | ✅ | Python |
| 统计分析 | ⚠️ | ✅ | Python |
| 数据清洗 | ❌ | ✅ | Python |
| 可视化 | ❌ | ✅ | Python |

---

## 最佳实践

1. **先用命令行探索**，了解数据结构
2. **复杂处理用 Python**，保持代码可维护
3. **保留原始数据**，清洗结果另存
4. **版本控制脚本**，可复现数据处理流程
5. **生成数据字典**，记录字段含义
