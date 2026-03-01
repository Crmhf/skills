# 前端状态管理指南

React/Vue 状态管理方案对比与选型建议。

## 目录

- [状态分类](#状态分类)
- [React 状态管理](#react-状态管理)
- [Vue 状态管理](#vue-状态管理)
- [选型决策树](#选型决策树)
- [最佳实践](#最佳实践)

---

## 状态分类

### 按作用域分类

| 类型 | 说明 | 示例 |
|------|------|------|
| **Local State** | 组件内部状态 | `useState`, `ref` |
| **Shared State** | 跨组件共享状态 | Context, Store |
| **Global State** | 应用级全局状态 | Redux, Pinia |
| **Server State** | 服务端数据缓存 | React Query, SWR |
| **URL State** | URL 参数状态 | Query params, Router |
| **Persistent State** | 持久化状态 | localStorage |

### 按更新频率分类

| 频率 | 说明 | 管理方式 |
|------|------|----------|
| 高频 | 实时更新，如输入框 | Local State |
| 中频 | 用户操作，如筛选 | Shared State |
| 低频 | 配置信息，如主题 | Global State |
| 静态 | 几乎不变，如用户信息 | Server Cache |

---

## React 状态管理

### 方案对比

| 方案 | 学习曲线 | 适用规模 | 特点 |
|------|----------|----------|------|
| **useState** | ⭐ | 小型 | 最简单，组件级 |
| **Context** | ⭐⭐ | 中小型 | 无需额外库，跨组件 |
| **Zustand** | ⭐ | 中小型 | 极简API，TypeScript友好 |
| **Jotai** | ⭐⭐ | 中小型 | 原子化，细粒度更新 |
| **Recoil** | ⭐⭐ | 中大型 | Facebook出品，原子化 |
| **Redux Toolkit** | ⭐⭐⭐ | 大型 | 生态丰富，可预测 |
| **MobX** | ⭐⭐ | 中大型 | 响应式，OOP风格 |

### Zustand 使用示例

```tsx
// store.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UserState {
  user: User | null;
  isLogin: boolean;
  login: (user: User) => void;
  logout: () => void;
  updateProfile: (profile: Partial<User>) => void;
}

export const useUserStore = create<UserState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isLogin: false,
        login: (user) => set({ user, isLogin: true }),
        logout: () => set({ user: null, isLogin: false }),
        updateProfile: (profile) =>
          set((state) => ({
            user: state.user ? { ...state.user, ...profile } : null,
          })),
      }),
      { name: 'user-storage' }
    )
  )
);

// 使用
function UserProfile() {
  const { user, updateProfile } = useUserStore();

  return (
    <div>
      <input
        value={user?.name}
        onChange={(e) => updateProfile({ name: e.target.value })}
      />
    </div>
  );
}
```

### Jotai 使用示例

```tsx
import { atom, useAtom, useSetAtom } from 'jotai';

// 基础原子
const countAtom = atom(0);

// 派生原子（只读）
const doubleCountAtom = atom((get) => get(countAtom) * 2);

// 派生原子（可写）
const incrementAtom = atom(null, (get, set) => {
  set(countAtom, get(countAtom) + 1);
});

function Counter() {
  const [count] = useAtom(countAtom);
  const [double] = useAtom(doubleCountAtom);
  const increment = useSetAtom(incrementAtom);

  return (
    <div>
      <p>Count: {count}</p>
      <p>Double: {double}</p>
      <button onClick={increment}>+1</button>
    </div>
  );
}
```

### Redux Toolkit 使用示例

```tsx
// store/slices/userSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const fetchUser = createAsyncThunk(
  'user/fetchUser',
  async (userId: string) => {
    const response = await api.getUser(userId);
    return response.data;
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState: {
    data: null as User | null,
    loading: false,
    error: null as string | null,
  },
  reducers: {
    clearUser: (state) => {
      state.data = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed';
      });
  },
});

export const { clearUser } = userSlice.actions;
export default userSlice.reducer;
```

---

## Vue 状态管理

### Pinia 使用示例

```typescript
// stores/user.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string>('');

  // Getters
  const isLogin = computed(() => !!token.value);
  const userName = computed(() => user.value?.name || 'Guest');

  // Actions
  async function login(credentials: Credentials) {
    const { data } = await api.login(credentials);
    user.value = data.user;
    token.value = data.token;
    localStorage.setItem('token', data.token);
  }

  function logout() {
    user.value = null;
    token.value = '';
    localStorage.removeItem('token');
  }

  return {
    user,
    token,
    isLogin,
    userName,
    login,
    logout,
  };
});

// 使用
<script setup>
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();

const handleLogin = async () => {
  await userStore.login({ username, password });
};
</script>
```

---

## 选型决策树

```
需要状态管理？
├── 只有本地状态？
│   └── 使用 useState / ref
├── 需要跨组件共享？
│   ├── 组件层级接近？
│   │   └── 使用 Context / provide-inject
│   └── 组件层级较远或全局？
│       ├── 中小型项目？
│       │   ├── React → Zustand / Jotai
│       │   └── Vue → Pinia
│       └── 大型复杂项目？
│           ├── React → Redux Toolkit
│           └── Vue → Pinia + 模块化
└── 需要服务端数据缓存？
    ├── React → React Query / SWR
    └── Vue → Vue Query / 自定义实现
```

---

## 最佳实践

### 1. 状态最小化原则

```tsx
// ❌ 不好的做法：存储计算值
const [fullName, setFullName] = useState('');
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// ✅ 好的做法：只存储原始值
const fullName = `${firstName} ${lastName}`;
```

### 2. 状态提升还是下沉？

| 场景 | 建议 |
|------|------|
| 只在组件内使用 | 保持 Local |
| 父子组件共享 | 提升到父组件 |
| 深层嵌套共享 | 使用 Context / 全局状态 |
| 应用级共享 | 使用全局状态管理 |

### 3. 异步状态管理

```tsx
// 使用 React Query 处理服务端状态
import { useQuery, useMutation } from '@tanstack/react-query';

function UserList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  });

  const mutation = useMutation({
    mutationFn: addUser,
    onSuccess: () => {
      // 自动刷新缓存
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  if (isLoading) return <Loading />;
  if (error) return <Error message={error.message} />;

  return (
    <>
      {data.map(user => <UserCard key={user.id} user={user} />)}
      <button onClick={() => mutation.mutate(newUser)}>
        Add User
      </button>
    </>
  );
}
```

### 4. 状态持久化

```tsx
// Zustand 持久化
import { persist, createJSONStorage } from 'zustand/middleware';

const useStore = create(
  persist(
    (set) => ({
      // state
    }),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        settings: state.settings,
        // 不持久化敏感数据
      }),
    }
  )
);
```

### 5. 状态调试

```tsx
// Redux DevTools 配置
const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV !== 'production',
});

// Zustand DevTools
const useStore = create(
  devtools(
    (set) => ({ /* state */ }),
    { name: 'MyStore' }
  )
);
```

---

## 检查清单

- [ ] 状态是否放在了正确的层级？
- [ ] 是否避免了 prop drilling？
- [ ] 服务端状态是否使用了专门的缓存方案？
- [ ] 敏感数据是否正确排除了持久化？
- [ ] 状态更新是否遵循不可变原则？
- [ ] 是否添加了适当的 TypeScript 类型？
