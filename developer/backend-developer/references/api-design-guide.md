# API 设计最佳实践

RESTful API 和 GraphQL 设计规范。

## 目录

- [RESTful 设计规范](#restful-设计规范)
- [版本控制](#版本控制)
- [错误处理](#错误处理)
- [安全防护](#安全防护)
- [GraphQL 设计](#graphql-设计)

---

## RESTful 设计规范

### URL 设计

```
# 资源命名
GET    /api/v1/users              # 列表
GET    /api/v1/users/{id}         # 详情
POST   /api/v1/users              # 创建
PUT    /api/v1/users/{id}         # 全量更新
PATCH  /api/v1/users/{id}         # 部分更新
DELETE /api/v1/users/{id}         # 删除

# 子资源
GET    /api/v1/users/{id}/orders  # 用户订单列表
POST   /api/v1/users/{id}/orders  # 创建用户订单

# 动作（非 CRUD）
POST   /api/v1/users/{id}/activate    # 激活用户
POST   /api/v1/orders/{id}/cancel     # 取消订单
POST   /api/v1/orders/{id}/refund     # 退款
```

### 请求/响应规范

```json
// 成功响应
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "name": "张三",
    "email": "zhangsan@example.com"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "requestId": "req_abc123"
}

// 列表响应
{
  "code": 200,
  "data": {
    "list": [...],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5
    }
  }
}

// 错误响应
{
  "code": 400,
  "message": "参数校验失败",
  "errors": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  ],
  "requestId": "req_def456"
}
```

### 分页规范

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @GetMapping
    public PageResult<User> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String sort) {

        // 参数校验
        if (size > 100) size = 100; // 最大 100 条

        Page<User> userPage = userService.page(
            new Page<>(page, size),
            new LambdaQueryWrapper<User>()
                .like(StringUtils.isNotBlank(keyword), User::getName, keyword)
                .orderByDesc(sort != null, User::getCreatedAt)
        );

        return PageResult.of(userPage);
    }
}
```

---

## 版本控制

### URL 版本控制

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserControllerV1 {
    // V1 实现
}

@RestController
@RequestMapping("/api/v2/users")
public class UserControllerV2 {
    // V2 实现，返回更多字段
}
```

### Header 版本控制

```java
@RequestMapping(value = "/api/users", headers = "API-VERSION=1")
public class UserControllerV1 {}

@RequestMapping(value = "/api/users", headers = "API-VERSION=2")
public class UserControllerV2 {}
```

---

## 错误处理

### 错误码规范

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | 400001 | 参数校验失败 |
| 400 | 400002 | JSON 解析错误 |
| 401 | 401001 | 未授权/Token 过期 |
| 403 | 403001 | 禁止访问 |
| 404 | 404001 | 资源不存在 |
| 409 | 409001 | 资源冲突 |
| 422 | 422001 | 业务逻辑错误 |
| 429 | 429001 | 请求过于频繁 |
| 500 | 500001 | 服务器内部错误 |

### 全局异常处理

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(
            MethodArgumentNotValidException e) {

        List<FieldError> errors = e.getBindingResult().getFieldErrors().stream()
            .map(error -> FieldError.builder()
                .field(error.getField())
                .message(error.getDefaultMessage())
                .build())
            .collect(Collectors.toList());

        ErrorResponse response = ErrorResponse.builder()
            .code(400001)
            .message("参数校验失败")
            .errors(errors)
            .timestamp(Instant.now())
            .build();

        return ResponseEntity.badRequest().body(response);
    }

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(BusinessException e) {
        ErrorResponse response = ErrorResponse.builder()
            .code(e.getCode())
            .message(e.getMessage())
            .timestamp(Instant.now())
            .build();

        return ResponseEntity.status(e.getHttpStatus()).body(response);
    }
}
```

---

## 安全防护

### 认证与授权

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeRequests()
                .antMatchers("/api/v1/auth/**").permitAll()
                .antMatchers("/api/v1/public/**").permitAll()
                .antMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(
                new JwtAuthenticationFilter(),
                UsernamePasswordAuthenticationFilter.class
            );

        return http.build();
    }
}
```

### 限流

```java
@Component
public class RateLimitInterceptor implements HandlerInterceptor {

    private final RateLimiter rateLimiter = RateLimiter.create(100.0);

    @Override
    public boolean preHandle(HttpServletRequest request,
                            HttpServletResponse response,
                            Object handler) throws Exception {
        if (!rateLimiter.tryAcquire()) {
            response.setStatus(429);
            response.getWriter().write("Too Many Requests");
            return false;
        }
        return true;
    }
}
```

### 输入验证

```java
@Data
public class CreateUserRequest {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 20, message = "用户名长度 3-20")
    private String username;

    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;

    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    @Min(value = 18, message = "年龄必须大于 18")
    @Max(value = 120, message = "年龄必须小于 120")
    private Integer age;
}
```

---

## GraphQL 设计

### Schema 定义

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  orders: [Order!]!
  createdAt: String!
}

type Order {
  id: ID!
  userId: ID!
  total: Float!
  status: OrderStatus!
  items: [OrderItem!]!
}

enum OrderStatus {
  PENDING
  PAID
  SHIPPED
  DELIVERED
  CANCELLED
}

type Query {
  user(id: ID!): User
  users(page: Int, size: Int): UserConnection!
  orders(userId: ID, status: OrderStatus): [Order!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!
}

input CreateUserInput {
  name: String!
  email: String!
  phone: String
}
```

### Resolver 实现

```java
@Component
public class UserResolver implements GraphQLQueryResolver, GraphQLMutationResolver {

    @Autowired
    private UserService userService;

    public User user(String id) {
        return userService.findById(id);
    }

    public UserConnection users(int page, int size) {
        return userService.findAll(page, size);
    }

    public User createUser(CreateUserInput input) {
        return userService.create(input);
    }

    // DataLoader 解决 N+1 问题
    @Autowired
    private OrderDataLoader orderDataLoader;

    public CompletableFuture<List<Order>> orders(User user) {
        return orderDataLoader.load(user.getId());
    }
}
```

---

## OpenAPI 文档

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0

paths:
  /api/v1/users:
    get:
      summary: 获取用户列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        200:
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
```

---

## 检查清单

- [ ] URL 是否符合 RESTful 规范？
- [ ] 是否做了版本控制？
- [ ] 错误响应格式是否统一？
- [ ] 是否实现了认证授权？
- [ ] 是否配置了限流？
- [ ] 输入参数是否做了校验？
- [ ] 是否生成了 API 文档？
