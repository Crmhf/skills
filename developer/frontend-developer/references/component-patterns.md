# 前端组件设计模式

常用的 React/Vue 组件设计模式和最佳实践。

## 目录

- [复合组件模式](#复合组件模式)
- [受控与非受控组件](#受控与非受控组件)
- [ render props 模式](#render-props-模式)
- [自定义 Hooks](#自定义-hooks)
- [性能优化模式](#性能优化模式)

---

## 复合组件模式

适用于复杂组件（如 Table、Form、Modal）的场景。

### 实现示例

```tsx
// Table 复合组件
const Table = <T extends Record<string, any>>({
  children,
  dataSource,
}: TableProps<T>) => {
  return (
    <TableContext.Provider value={{ dataSource }}>
      <table className="table">{children}</table>
    </TableContext.Provider>
  );
};

Table.Column = <T,>({ dataIndex, title, render }: ColumnProps<T>) => {
  const { dataSource } = useContext(TableContext);
  return (
    <th>
      {title}
      {dataSource.map((record, index) => (
        <td key={index}>
          {render ? render(record[dataIndex], record) : record[dataIndex]}
        </td>
      ))}
    </th>
  );
};

// 使用方式
<Table dataSource={users}>
  <Table.Column dataIndex="name" title="姓名" />
  <Table.Column
    dataIndex="status"
    title="状态"
    render={(status) => <Badge status={status} />}
  />
</Table>
```

---

## 受控与非受控组件

### 受控组件

组件状态完全由父组件控制。

```tsx
interface InputProps {
  value: string;
  onChange: (value: string) => void;
}

const ControlledInput = ({ value, onChange }: InputProps) => {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  );
};
```

### 非受控组件

组件内部管理自己的状态。

```tsx
const UncontrolledInput = ({ defaultValue = '' }: { defaultValue?: string }) => {
  const [value, setValue] = useState(defaultValue);
  return (
    <input
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  );
};
```

### 混合模式

支持受控和非受控两种模式。

```tsx
interface HybridInputProps {
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
}

const HybridInput = ({ value, defaultValue, onChange }: HybridInputProps) => {
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue || '');

  const handleChange = (newValue: string) => {
    if (!isControlled) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
  };

  return (
    <input
      value={isControlled ? value : internalValue}
      onChange={(e) => handleChange(e.target.value)}
    />
  );
};
```

---

## Render Props 模式

通过函数 prop 共享组件内部状态。

```tsx
interface ToggleProps {
  children: (props: { on: boolean; toggle: () => void }) => React.ReactNode;
}

const Toggle = ({ children }: ToggleProps) => {
  const [on, setOn] = useState(false);
  const toggle = () => setOn(!on);

  return <>{children({ on, toggle })}</>;
};

// 使用方式
<Toggle>
  {({ on, toggle }) => (
    <button onClick={toggle}>
      {on ? 'ON' : 'OFF'}
    </button>
  )}
</Toggle>
```

---

## 自定义 Hooks

### 常用 Hooks 列表

| Hook | 用途 | 复杂度 |
|------|------|--------|
| `useFetch` | 数据获取 | ⭐⭐ |
| `useLocalStorage` | 本地存储同步 | ⭐⭐ |
| `useDebounce` | 防抖处理 | ⭐ |
| `useThrottle` | 节流处理 | ⭐ |
| `useIntersectionObserver` | 视口检测 | ⭐⭐ |
| `useMediaQuery` | 响应式断点 | ⭐ |
| `useForm` | 表单管理 | ⭐⭐⭐ |
| `useInfiniteScroll` | 无限滚动 | ⭐⭐ |

### useFetch 实现

```tsx
interface UseFetchOptions<T> {
  url: string;
  initialData?: T;
  enabled?: boolean;
}

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

function useFetch<T>({ url, initialData, enabled = true }: UseFetchOptions<T>): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(initialData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Network error');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    if (enabled) fetchData();
  }, [fetchData, enabled]);

  return { data, loading, error, refetch: fetchData };
}
```

---

## 性能优化模式

### 1. 虚拟列表

大数据量渲染优化。

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
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

### 2. 懒加载组件

```tsx
const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <HeavyComponent />
    </Suspense>
  );
}
```

### 3. 记忆化计算

```tsx
import { useMemo, useCallback } from 'react';

function DataTable({ data, filter }: Props) {
  // 记忆化过滤结果
  const filteredData = useMemo(() => {
    return data.filter(item => item.name.includes(filter));
  }, [data, filter]);

  // 记忆化回调函数
  const handleSort = useCallback((key: string) => {
    // 排序逻辑
  }, []);

  return <Table data={filteredData} onSort={handleSort} />;
}
```

---

## 组件设计检查清单

- [ ] 是否明确定义了 Props 接口？
- [ ] 是否处理了 loading 状态？
- [ ] 是否处理了 error 状态？
- [ ] 是否支持受控/非受控模式？
- [ ] 是否进行了必要的性能优化（memo/useMemo/useCallback）？
- [ ] 是否提供了合理的默认值？
- [ ] 是否支持无障碍访问（ARIA）？
