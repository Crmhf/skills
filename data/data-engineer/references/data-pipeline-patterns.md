# 数据管道设计模式

数据工程管道设计模式与最佳实践。

## 目录

- [ETL vs ELT](#etl-vs-elt)
- [批处理 vs 流处理](#批处理-vs-流处理)
- [数据质量](#数据质量)

---

## ETL vs ELT

### 对比

| 维度 | ETL | ELT |
|------|-----|-----|
| 转换位置 | 中间层 | 目标仓库 |
| 适用场景 | 传统数仓 | 云数据湖 |
| 灵活性 | 较低 | 较高 |
| 性能 | 预处理 | 利用仓库计算 |

### ELT 示例 (dbt)

```sql
-- models/staging/stg_orders.sql
with source as (
    select * from {{ source('raw', 'orders') }}
),
renamed as (
    select
        id as order_id,
        user_id,
        amount,
        created_at
    from source
)
select * from renamed
```

---

## 批处理 vs 流处理

### 选择矩阵

| 场景 | 批处理 | 流处理 |
|------|--------|--------|
| 历史分析 | ✅ | ❌ |
| 实时监控 | ❌ | ✅ |
| 资源效率 | ✅ | ❌ |
| 延迟要求 | 分钟级 | 秒级 |

### 流处理示例 (Kafka Streams)

```java
StreamsBuilder builder = new StreamsBuilder();

builder.stream("orders")
    .groupByKey()
    .windowedBy(TimeWindows.of(Duration.ofMinutes(5)))
    .count()
    .toStream()
    .to("order-counts");
```

---

## 数据质量

### 检查维度

| 维度 | 说明 | 示例 |
|------|------|------|
| 完整性 | 非空检查 | 用户ID不能为空 |
| 准确性 | 值域检查 | 年龄在0-150之间 |
| 一致性 | 关联检查 | 订单金额=单价×数量 |
| 及时性 | 延迟检查 | 数据延迟<1小时 |

### Great Expectations 示例

```python
import great_expectations as gx

validator.expect_column_values_to_not_be_null("user_id")
validator.expect_column_values_to_be_between("age", 0, 150)
validator.expect_column_pair_values_to_be_equal(
    column_A="total_amount",
    column_B="price * quantity"
)
```

---

## 检查清单

- [ ] 数据管道是否可监控？
- [ ] 失败是否有重试机制？
- [ ] 数据质量检查是否完善？
- [ ] 是否有数据血缘追踪？
