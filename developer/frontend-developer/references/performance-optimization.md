# 前端性能优化指南

系统化的 Web 性能优化策略与实践。

## 目录

- [性能指标](#性能指标)
- [加载优化](#加载优化)
- [渲染优化](#渲染优化)
- [网络优化](#网络优化)
- [缓存策略](#缓存策略)

---

## 性能指标

### Core Web Vitals

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **LCP** | ≤2.5s | 最大内容绘制 |
| **FID** | ≤100ms | 首次输入延迟 |
| **CLS** | ≤0.1 | 累积布局偏移 |
| **FCP** | ≤1.8s | 首次内容绘制 |
| **TTFB** | ≤800ms | 首字节时间 |
| **INP** | ≤200ms | 交互到下一次绘制 |

### 测量工具

```bash
# Lighthouse CLI
npm install -g lighthouse
lighthouse https://example.com --preset=desktop

# Web Vitals Chrome Extension
# 安装扩展实时监测

# 代码中测量
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getLCP(console.log);
```

---

## 加载优化

### 资源预加载

```html
<!-- DNS预解析 -->
<link rel="dns-prefetch" href="//api.example.com">

<!-- 预连接 -->
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- 预加载关键资源 -->
<link rel="preload" href="/critical.css" as="style">
<link rel="preload" href="/font.woff2" as="font" crossorigin>

<!-- 预获取下一页 -->
<link rel="prefetch" href="/next-page.js">

<!-- 预渲染 -->
<link rel="prerender" href="/next-page">
```

### 代码分割

```tsx
// React.lazy + Suspense
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}

// 动态导入
async function loadChart() {
  const { Chart } = await import('./components/Chart');
  return Chart;
}
```

### 图片优化

```tsx
// 现代格式 + 响应式
<picture>
  <source
    srcSet="image.avif"
    type="image/avif"
  >
  <source
    srcSet="image.webp"
    type="image/webp"
  >
  <img
    src="image.jpg"
    alt="描述"
    loading="lazy"
    decoding="async"
    width="800"
    height="600"
  >
</picture>

// 使用 CDN 图片优化服务
// https://cdn.example.com/image.jpg?w=800&h=600&fit=crop&fm=webp
```

---

## 渲染优化

### 避免重排重绘

```tsx
// ❌ 不好的做法：多次修改样式
const element = document.getElementById('box');
element.style.width = '100px';
element.style.height = '100px';
element.style.margin = '10px';

// ✅ 好的做法：使用 CSS 类或批量修改
// 方案1：使用 class
element.classList.add('box-large');

// 方案2：使用 CSS 变量
element.style.cssText = 'width: 100px; height: 100px; margin: 10px;';
```

### React 渲染优化

```tsx
import { memo, useMemo, useCallback } from 'react';

// 1. 组件记忆化
const ExpensiveComponent = memo(({ data, onUpdate }) => {
  return <div>{/* 复杂渲染 */}</div>;
}, (prevProps, nextProps) => {
  // 自定义比较函数
  return prevProps.id === nextProps.id;
});

// 2. 值记忆化
function DataTable({ data, filter }) {
  const filteredData = useMemo(() => {
    return data.filter(item => item.includes(filter));
  }, [data, filter]);

  // 3. 函数记忆化
  const handleSort = useCallback((key: string) => {
    // 排序逻辑
  }, []);

  return <Table data={filteredData} onSort={handleSort} />;
}
```

### 虚拟列表

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
    overscan: 5, // 预渲染行数
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: virtualItem.size,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 网络优化

### 请求优化

```typescript
// 1. 请求合并
const [users, posts, comments] = await Promise.all([
  fetchUsers(),
  fetchPosts(),
  fetchComments(),
]);

// 2. 防抖/节流
import { debounce, throttle } from 'lodash-es';

const debouncedSearch = debounce((query) => {
  searchAPI(query);
}, 300);

const throttledScroll = throttle(() => {
  handleScroll();
}, 100);

// 3. 请求取消
const controller = new AbortController();

fetch('/api/data', { signal: controller.signal })
  .then(response => response.json())
  .then(data => console.log(data));

// 组件卸载时取消
useEffect(() => {
  return () => controller.abort();
}, []);
```

### 数据压缩

```typescript
// 启用 Brotli/Gzip 压缩
// nginx.conf
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;

// 客户端支持
// Accept-Encoding: gzip, deflate, br
```

---

## 缓存策略

### HTTP 缓存

```nginx
# 静态资源长期缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# HTML 不缓存
location ~* \.html$ {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}

# API 短期缓存
location /api/ {
    expires 5m;
    add_header Cache-Control "public, must-revalidate";
}
```

### Service Worker 缓存

```typescript
// service-worker.ts
const CACHE_NAME = 'app-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/js/main.js',
  '/static/css/main.css',
];

// 安装时缓存静态资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

// 拦截请求
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // 缓存优先
      if (response) {
        return response;
      }
      return fetch(event.request);
    })
  );
});
```

---

## 性能检查清单

### 开发阶段

- [ ] 使用 Lighthouse 跑分 > 90
- [ ] 图片已优化（WebP/AVIF，懒加载）
- [ ] 关键 CSS 内联
- [ ] JS 代码已分割
- [ ] 第三方库按需导入

### 生产阶段

- [ ] 启用 Gzip/Brotli 压缩
- [ ] 配置 CDN
- [ ] 静态资源长期缓存
- [ ] 启用 HTTP/2
- [ ] 监控 Core Web Vitals
