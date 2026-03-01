# 微服务设计模式

微服务架构的核心模式与最佳实践。

## 目录

- [服务拆分策略](#服务拆分策略)
- [服务通信模式](#服务通信模式)
- [数据管理](#数据管理)
- [服务治理](#服务治理)
- [故障处理](#故障处理)

---

## 服务拆分策略

### 按领域拆分 (DDD)

```
电商系统示例:
├── 用户服务 (User Domain)
│   ├── 用户注册/登录
│   ├── 用户资料管理
│   └── 权限管理
├── 订单服务 (Order Domain)
│   ├── 订单创建
│   ├── 订单状态管理
│   └── 订单查询
├── 商品服务 (Product Domain)
│   ├── 商品信息管理
│   ├── 库存管理
│   └── 价格管理
├── 支付服务 (Payment Domain)
│   ├── 支付处理
│   ├── 退款处理
│   └── 对账
└── 库存服务 (Inventory Domain)
    ├── 库存扣减
    ├── 库存预占
    └── 库存同步
```

### 拆分时考虑的因素

| 因素 | 说明 | 示例 |
|------|------|------|
| 业务边界 | 独立的业务能力 | 订单、支付、库存 |
| 数据隔离 | 独立的数据存储 | 每个服务独立数据库 |
| 团队结构 | 康威定律 | 2-pizza team |
| 变更频率 | 高频变更独立部署 | 促销服务独立 |
| 伸缩需求 | 不同的扩展需求 | 订单服务多实例 |

---

## 服务通信模式

### 同步通信

```java
// RESTful API 调用
@Service
public class OrderService {
    @Autowired
    private InventoryClient inventoryClient;

    public Order createOrder(OrderRequest request) {
        // 同步调用库存服务
        InventoryResult result = inventoryClient.deduct(
            request.getSkuId(),
            request.getQuantity()
        );

        if (result.isSuccess()) {
            return orderRepository.save(request.toOrder());
        }
        throw new InsufficientStockException();
    }
}

// OpenFeign 客户端
@FeignClient(name = "inventory-service")
public interface InventoryClient {
    @PostMapping("/api/inventory/deduct")
    InventoryResult deduct(@RequestParam String skuId,
                          @RequestParam Integer quantity);
}
```

### 异步通信

```java
// 事件驱动架构
@Service
public class OrderEventPublisher {
    @Autowired
    private KafkaTemplate<String, OrderEvent> kafkaTemplate;

    public void publishOrderCreated(Order order) {
        OrderEvent event = OrderEvent.builder()
            .orderId(order.getId())
            .userId(order.getUserId())
            .amount(order.getTotalAmount())
            .timestamp(System.currentTimeMillis())
            .build();

        kafkaTemplate.send("order-created", event);
    }
}

// 事件消费者
@Component
public class InventoryEventListener {
    @KafkaListener(topics = "order-created")
    public void onOrderCreated(OrderEvent event) {
        inventoryService.deductStock(event.getOrderId(), event.getItems());
    }
}
```

### gRPC 高性能通信

```protobuf
// inventory.proto
syntax = "proto3";

service InventoryService {
    rpc DeductStock(DeductRequest) returns (DeductResponse);
    rpc CheckStock(CheckRequest) returns (CheckResponse);
}

message DeductRequest {
    string sku_id = 1;
    int32 quantity = 2;
}

message DeductResponse {
    bool success = 1;
    string message = 2;
}
```

---

## 数据管理

### 数据库每服务模式

```yaml
# 每个服务独立数据库
services:
  order-service:
    database: order_db
    type: MySQL

  user-service:
    database: user_db
    type: PostgreSQL

  product-service:
    database: product_db
    type: MongoDB
```

### 分布式事务方案

| 方案 | 一致性 | 性能 | 复杂度 | 适用场景 |
|------|--------|------|--------|----------|
| 2PC | 强一致 | 低 | 中 | 传统金融 |
| TCC | 最终一致 | 高 | 高 | 电商核心交易 |
| Saga | 最终一致 | 高 | 中 | 长事务流程 |
| 本地消息表 | 最终一致 | 高 | 低 | 一般业务 |

### Saga 模式实现

```java
// 编排式 Saga
@Service
public class OrderSaga {
    @Autowired
    private SagaOrchestrator orchestrator;

    public void createOrder(OrderContext context) {
        SagaDefinition saga = SagaBuilder.create()
            .step("createOrder")
                .action(this::createOrderAction)
                .compensation(this::cancelOrderCompensation)
            .step("deductStock")
                .action(this::deductStockAction)
                .compensation(this::restoreStockCompensation)
            .step("processPayment")
                .action(this::processPaymentAction)
                .compensation(this::refundPaymentCompensation)
            .build();

        orchestrator.execute(saga, context);
    }
}
```

---

## 服务治理

### 服务注册与发现

```yaml
# Consul 配置
spring:
  cloud:
    consul:
      host: localhost
      port: 8500
      discovery:
        service-name: ${spring.application.name}
        health-check-path: /actuator/health
        health-check-interval: 10s
```

### 负载均衡

```java
@Configuration
public class LoadBalanceConfig {

    @Bean
    @LoadBalanced
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    // 自定义负载均衡策略
    @Bean
    public ReactorLoadBalancer<ServiceInstance> randomLoadBalancer(
            Environment environment,
            LoadBalancerClientFactory clientFactory) {
        String name = environment.getProperty(LoadBalancerClientFactory.PROPERTY_NAME);
        return new RandomLoadBalancer(
            clientFactory.getLazyProvider(name, ServiceInstanceListSupplier.class),
            name
        );
    }
}
```

### 熔断降级

```java
@Service
public class PaymentService {

    @CircuitBreaker(
        name = "payment",
        fallbackMethod = "processPaymentFallback"
    )
    public PaymentResult processPayment(PaymentRequest request) {
        return paymentClient.charge(request);
    }

    // 降级方法
    public PaymentResult processPaymentFallback(
            PaymentRequest request,
            Exception ex) {
        log.warn("Payment service fallback", ex);

        // 保存到待处理队列，稍后重试
        paymentQueue.add(request);

        return PaymentResult.builder()
            .status("PENDING")
            .message("Payment queued for retry")
            .build();
    }
}
```

### 限流

```java
@Component
public class RateLimitFilter implements GatewayFilter {

    private final RateLimiter rateLimiter = RateLimiter.create(100.0); // 100 QPS

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!rateLimiter.tryAcquire()) {
            exchange.getResponse().setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
            return exchange.getResponse().setComplete();
        }
        return chain.filter(exchange);
    }
}
```

---

## 故障处理

### 重试策略

```java
@Configuration
public class RetryConfig {

    @Bean
    public RetryTemplate retryTemplate() {
        RetryTemplate template = new RetryTemplate();

        // 重试策略: 最多3次
        template.setRetryPolicy(new SimpleRetryPolicy(3));

        // 退避策略: 指数退避
        ExponentialBackOffPolicy backOff = new ExponentialBackOffPolicy();
        backOff.setInitialInterval(1000);
        backOff.setMultiplier(2);
        backOff.setMaxInterval(10000);
        template.setBackOffPolicy(backOff);

        return template;
    }
}

// 使用
@Service
public class RemoteService {
    @Autowired
    private RetryTemplate retryTemplate;

    public Data fetchData() {
        return retryTemplate.execute(context -> {
            return remoteClient.getData();
        });
    }
}
```

### 链路追踪

```java
@Service
public class OrderService {
    @Autowired
    private Tracer tracer;

    public void processOrder(Order order) {
        Span span = tracer.nextSpan()
            .name("processOrder")
            .tag("order.id", order.getId())
            .start();

        try (Tracer.SpanInScope ws = tracer.withSpanInScope(span)) {
            validateOrder(order);
            saveOrder(order);
            notifyUser(order);
        } catch (Exception e) {
            span.error(e);
            throw e;
        } finally {
            span.end();
        }
    }
}
```

---

## 检查清单

- [ ] 服务边界是否清晰？
- [ ] 数据库是否独立？
- [ ] 服务间通信是否选择了合适的方式？
- [ ] 是否实现了熔断降级？
- [ ] 是否配置了限流？
- [ ] 是否实现了分布式事务？
- [ ] 是否有链路追踪？
- [ ] 是否有健康检查？
