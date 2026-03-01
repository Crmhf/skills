# 数据库性能优化指南

关系型数据库和 NoSQL 的性能优化策略。

## 目录

- [索引优化](#索引优化)
- [查询优化](#查询优化)
- [架构优化](#架构优化)
- [连接池优化](#连接池优化)

---

## 索引优化

### 索引设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| 最左前缀 | 复合索引按查询顺序 | `(a,b,c)` 支持 `a`, `a,b`, `a,b,c` |
| 选择性 | 高区分度列优先 | 身份证 > 性别 |
| 覆盖索引 | 避免回表 | `SELECT name FROM user WHERE id = 1` |
| 避免冗余 | 不创建重复索引 | `(a)` 和 `(a,b)` 保留后者 |

### 索引创建示例

```sql
-- 复合索引
CREATE INDEX idx_user_status_created
ON users(status, created_at);

-- 覆盖索引
CREATE INDEX idx_order_user_amount
ON orders(user_id, amount, status, created_at);

-- 唯一索引
CREATE UNIQUE INDEX idx_user_email
ON users(email);

-- 前缀索引
CREATE INDEX idx_user_name
ON users(name(10));
```

### 执行计划分析

```sql
-- MySQL
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE user_id = 123
AND created_at > '2024-01-01'
ORDER BY created_at DESC
LIMIT 10;

-- 关键字段解读
-- type: ALL(全表) → index(索引) → range(范围) → ref(等值) → const(主键)
-- key: 实际使用的索引
-- rows: 扫描行数
-- Extra: Using index(覆盖) / Using where / Using filesort(需优化)
```

---

## 查询优化

### 慢查询优化

```sql
-- 开启慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- 分析慢查询
SELECT * FROM mysql.slow_log
WHERE start_time > DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY query_time DESC
LIMIT 10;
```

### SQL 优化技巧

```sql
-- ❌ 避免 SELECT *
SELECT * FROM users WHERE age > 18;

-- ✅ 只查询需要的列
SELECT id, name, email FROM users WHERE age > 18;

-- ❌ 避免在索引列上使用函数
SELECT * FROM users WHERE YEAR(created_at) = 2024;

-- ✅ 使用范围查询
SELECT * FROM users
WHERE created_at >= '2024-01-01'
AND created_at < '2025-01-01';

-- ❌ 避免隐式类型转换
SELECT * FROM users WHERE phone = 13800138000;

-- ✅ 使用正确的类型
SELECT * FROM users WHERE phone = '13800138000';
```

### 分页优化

```sql
-- ❌ 深度分页问题
SELECT * FROM orders
ORDER BY created_at DESC
LIMIT 1000000, 10;

-- ✅ 使用覆盖索引 + 延迟关联
SELECT * FROM orders o
JOIN (
    SELECT id FROM orders
    ORDER BY created_at DESC
    LIMIT 1000000, 10
) tmp ON o.id = tmp.id;

-- ✅ 基于游标分页
SELECT * FROM orders
WHERE created_at < '2024-01-15 10:00:00'
ORDER BY created_at DESC
LIMIT 10;
```

---

## 架构优化

### 读写分离

```java
@Configuration
public class DataSourceConfig {

    @Bean
    public DataSource routingDataSource() {
        DynamicRoutingDataSource routing = new DynamicRoutingDataSource();

        Map<Object, Object> targets = new HashMap<>();
        targets.put("master", masterDataSource());
        targets.put("slave1", slave1DataSource());
        targets.put("slave2", slave2DataSource());

        routing.setTargetDataSources(targets);
        routing.setDefaultTargetDataSource(masterDataSource());

        return routing;
    }
}

// 注解方式
@Service
public class OrderService {

    @Master  // 强制走主库
    public void createOrder(Order order) {
        orderRepository.save(order);
    }

    @Slave   // 走从库
    public List<Order> getOrders(Long userId) {
        return orderRepository.findByUserId(userId);
    }
}
```

### 分库分表

```yaml
# ShardingSphere 配置
spring:
  shardingsphere:
    datasource:
      names: ds0, ds1
      ds0: ...
      ds1: ...
    sharding:
      tables:
        order:
          actual-data-nodes: ds$->{0..1}.order_$->{0..15}
          table-strategy:
            inline:
              sharding-column: user_id
              algorithm-expression: order_$->{user_id % 16}
          database-strategy:
            inline:
              sharding-column: user_id
              algorithm-expression: ds$->{user_id % 2}
```

### 缓存策略

```java
@Service
public class ProductService {

    @Autowired
    private CacheManager cacheManager;

    // 本地缓存 (Caffeine)
    @Cacheable(value = "product", key = "#id", cacheManager = "localCacheManager")
    public Product getById(Long id) {
        return productRepository.findById(id).orElse(null);
    }

    // 分布式缓存 (Redis)
    @Cacheable(value = "product:detail", key = "#id")
    public ProductDetail getDetail(Long id) {
        return productRepository.findDetailById(id);
    }

    // 缓存更新
    @CacheEvict(value = "product", key = "#product.id")
    @CachePut(value = "product:detail", key = "#product.id")
    public Product update(Product product) {
        return productRepository.save(product);
    }
}
```

---

## 连接池优化

### HikariCP 配置

```yaml
spring:
  datasource:
    hikari:
      # 基础配置
      jdbc-url: jdbc:mysql://localhost:3306/mydb
      username: root
      password: password
      driver-class-name: com.mysql.cj.jdbc.Driver

      # 连接池配置
      minimum-idle: 10           # 最小空闲连接
      maximum-pool-size: 50      # 最大连接数
      idle-timeout: 600000       # 空闲连接超时时间(ms)
      max-lifetime: 1800000      # 连接最大生命周期(ms)
      connection-timeout: 30000  # 连接超时时间(ms)

      # 性能优化
      prepStmtCacheSize: 250
      prepStmtCacheSqlLimit: 2048
      cachePrepStmts: true
      useServerPrepStmts: true
```

### 连接数计算公式

```
连接数 = ((核心数 * 2) + 有效磁盘数)

示例:
- 8核CPU, SSD磁盘
- 理论最优: (8 * 2) + 1 = 17
- 实际设置: 20-30 (考虑并发和等待时间)
```

---

## 检查清单

- [ ] 慢查询是否已优化？
- [ ] 索引是否合理创建？
- [ ] 是否避免了全表扫描？
- [ ] 连接池参数是否调优？
- [ ] 大表是否考虑分库分表？
- [ ] 读多写少场景是否使用读写分离？
- [ ] 热点数据是否添加缓存？
