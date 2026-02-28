# 技术评估框架

系统化的技术选型与评估方法论。

---

## 1. 评估流程

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  需求澄清   │ → │  方案调研   │ → │  原型验证   │
└─────────────┘   └─────────────┘   └──────┬──────┘
                                          │
┌─────────────┐   ┌─────────────┐   ┌─────▼───────┐
│  实施跟踪   │ ← │  决策记录   │ ← │  评估决策   │
└─────────────┘   └─────────────┘   └─────────────┘
```

### 1.1 需求澄清

**功能需求清单**
- [ ] 核心功能要求
- [ ] 性能指标要求（QPS、延迟、吞吐）
- [ ] 可用性要求（SLA、RTO、RPO）
- [ ] 安全合规要求
- [ ] 扩展性要求（数据增长预期）

**约束条件**
- [ ] 预算限制
- [ ] 时间限制
- [ ] 团队技能栈
- [ ] 现有系统集成要求

### 1.2 方案调研

**调研清单**
- [ ] 主流开源方案
- [ ] 商业方案对比
- [ ] 大厂实践经验
- [ ] 社区活跃度（GitHub stars、贡献者数量）
- [ ] 文档完善度
- [ ] 长期维护承诺

---

## 2. 评估维度体系

### 2.1 技术维度（40%）

| 子维度 | 权重 | 评估要点 |
|-------|------|---------|
| 功能性 | 15% | 是否满足全部核心需求 |
| 性能 | 15% | 基准测试、资源占用 |
| 可靠性 | 10% | 稳定性、成熟度 |

### 2.2 运维维度（25%）

| 子维度 | 权重 | 评估要点 |
|-------|------|---------|
| 可扩展性 | 10% | 水平扩展能力 |
| 可观测性 | 10% | 监控、日志、追踪 |
| 运维复杂度 | 5% | 部署难度、学习成本 |

### 2.3 生态维度（20%）

| 子维度 | 权重 | 评估要点 |
|-------|------|---------|
| 社区活跃度 | 10% | GitHub 活跃度、版本发布频率 |
| 文档质量 | 5% | 官方文档、教程丰富度 |
| 集成能力 | 5% | 与现有技术栈兼容性 |

### 2.4 商业维度（15%）

| 子维度 | 权重 | 评估要点 |
|-------|------|---------|
| 总拥有成本 | 10% | 许可费、运维成本、人力成本 |
| 供应商风险 | 5% | 供应商锁定、迁移成本 |

---

## 3. 评分卡模板

### 3.1 消息队列选型示例

| 维度 | 权重 | Kafka | RocketMQ | Pulsar | RabbitMQ |
|-----|------|-------|---------|--------|----------|
| **吞吐量** | 15% | 10 | 9 | 9 | 6 |
| **延迟** | 10% | 7 | 8 | 9 | 8 |
| **可靠性** | 15% | 9 | 9 | 9 | 8 |
| **扩展性** | 10% | 9 | 8 | 10 | 6 |
| **运维复杂度** | 10% | 6 | 8 | 6 | 9 |
| **社区活跃度** | 10% | 10 | 7 | 6 | 8 |
| **云原生支持** | 10% | 7 | 7 | 10 | 6 |
| **成本** | 10% | 9 | 9 | 8 | 9 |
| **团队熟悉度** | 10% | 7 | 8 | 5 | 7 |
| **加权总分** | | **8.3** | **8.15** | **8.1** | **7.25** |

**评分说明**
- 10: 极佳，行业领先
- 7-9: 良好，满足需求
- 4-6: 一般，有局限
- 1-3: 差，不建议使用

### 3.2 数据库选型示例

| 维度 | 权重 | PostgreSQL | MySQL | MongoDB | TiDB |
|-----|------|-----------|-------|---------|------|
| **事务支持** | 20% | 10 | 9 | 6 | 9 |
| **查询能力** | 15% | 9 | 8 | 7 | 8 |
| **扩展性** | 15% | 7 | 7 | 8 | 10 |
| **JSON支持** | 10% | 9 | 6 | 10 | 7 |
| **运维成本** | 15% | 8 | 9 | 8 | 6 |
| **生态成熟度** | 15% | 9 | 10 | 8 | 6 |
| **团队熟悉度** | 10% | 7 | 9 | 7 | 5 |
| **加权总分** | | **8.55** | **8.25** | **7.55** | **7.45** |

---

## 4. 原型验证方法

### 4.1 性能基准测试

```python
# 基准测试框架示例
import time
import asyncio
from statistics import mean, median

class Benchmark:
    def __init__(self, name):
        self.name = name
        self.results = []

    async def run(self, func, *args, iterations=1000, concurrency=10):
        """运行基准测试"""
        semaphore = asyncio.Semaphore(concurrency)

        async def wrapped():
            async with semaphore:
                start = time.perf_counter()
                await func(*args)
                return time.perf_counter() - start

        tasks = [wrapped() for _ in range(iterations)]
        self.results = await asyncio.gather(*tasks)
        return self.report()

    def report(self):
        """生成测试报告"""
        return {
            'name': self.name,
            'iterations': len(self.results),
            'total_time': sum(self.results),
            'avg_latency': mean(self.results),
            'p50_latency': median(self.results),
            'p99_latency': sorted(self.results)[int(len(self.results) * 0.99)],
            'throughput': len(self.results) / sum(self.results)
        }
```

### 4.2 故障场景测试

**测试场景清单**

| 场景 | 测试方法 | 通过标准 |
|-----|---------|---------|
| 单节点故障 | kill -9 进程 | 自动切换，数据不丢 |
| 网络分区 | iptables 隔离 | 脑裂防护，一致性保持 |
| 高负载 | 压力测试 | 降级策略生效 |
| 数据恢复 | 备份恢复测试 | RPO/RTO 达标 |
| 升级兼容性 | 滚动升级 | 零停机，回滚可行 |

---

## 5. 决策矩阵

### 5.1 通用决策树

```
是否需要强一致性？
├── 是 → 关系型数据库
│   ├── 需要复杂查询？
│   │   ├── 是 → PostgreSQL
│   │   └── 否 → MySQL
│   └── 需要水平扩展？
│       ├── 是 → TiDB / CockroachDB
│       └── 否 → PostgreSQL / MySQL
└── 否 → NoSQL
    ├── 需要事务？
    │   ├── 是 → MongoDB
    │   └── 否 → 其他
    ├── 数据模型？
    │   ├── 文档 → MongoDB
    │   ├── 键值 → Redis
    │   ├── 列族 → Cassandra
    │   └── 图 → Neo4j
    └── 查询模式？
        ├── 全文检索 → Elasticsearch
        └── 时序数据 → InfluxDB
```

### 5.2 场景化推荐

**初创公司 MVP（追求速度）**
- 数据库: PostgreSQL（功能全，免维护）
- 缓存: Redis
- 搜索: PostgreSQL 全文检索
- 队列: Redis / 云服务商队列

**高并发电商（追求性能）**
- 数据库: MySQL + 分库分表 / TiDB
- 缓存: Redis Cluster
- 搜索: Elasticsearch
- 队列: RocketMQ / Kafka

**金融支付（追求一致性和可靠性）**
- 数据库: PostgreSQL / Oracle / TiDB
- 缓存: Redis（持久化配置）
- 搜索: Elasticsearch
- 队列: RocketMQ（事务消息）

**SaaS 多租户（追求扩展性）**
- 数据库: PostgreSQL / CockroachDB
- 缓存: Redis Cluster
- 搜索: Elasticsearch
- 队列: Kafka / Pulsar

---

## 6. 常见技术选型场景

### 6.1 编程语言/运行时

| 场景 | 首选 | 备选 | 说明 |
|-----|------|------|------|
| 后端 API | Go / Java | Node.js / Python | 性能与生态平衡 |
| 数据处理 | Python / Scala | Go / Java | 丰富的数据生态 |
| 前端应用 | TypeScript | JavaScript | 类型安全 |
| 移动应用 | Kotlin / Swift | Flutter | 原生体验 |
| 系统编程 | Rust / Go | C++ | 安全与性能 |

### 6.2 框架选型

| 场景 | 首选 | 备选 |
|-----|------|------|
| Web 框架 (Java) | Spring Boot | Quarkus / Micronaut |
| Web 框架 (Go) | Gin / Echo | Fiber |
| Web 框架 (Python) | FastAPI | Django / Flask |
| RPC 框架 | gRPC | Thrift / Dubbo |

### 6.3 基础设施

| 场景 | 首选 | 备选 |
|-----|------|------|
| 容器编排 | Kubernetes | Docker Swarm / Nomad |
| 服务网格 | Istio | Linkerd |
| 监控 | Prometheus + Grafana | Datadog |
| 日志 | ELK / Loki | Splunk |
| CI/CD | GitLab CI / GitHub Actions | Jenkins / ArgoCD |

---

## 7. 决策检查清单

### 决策前
- [ ] 需求已充分理解并文档化
- [ ] 至少对比了 3 个候选方案
- [ ] 关键利益相关者已参与讨论
- [ ] 进行了原型验证或 POC
- [ ] 风险评估已完成

### 决策中
- [ ] 使用结构化评估框架
- [ ] 记录了决策过程和思考
- [ ] 明确了决策的有效期限
- [ ] 制定了回退方案

### 决策后
- [ ] 决策已记录在 ADR 中
- [ ] 团队已沟通和培训
- [ ] 实施计划已制定
- [ ] 设置了回顾检查点
- [ ] 指标收集已配置

---

## 8. 工具与资源

### 评估工具
- **技术雷达**: ThoughtWorks Radar
- **技术对比**: StackShare, LibHunt
- **GitHub 统计**: Star History, OpenHub

### 参考资料
- **系统设计**: System Design Primer
- **性能基准**: TechEmpower Framework Benchmarks
- **云原生**: CNCF Cloud Native Landscape
