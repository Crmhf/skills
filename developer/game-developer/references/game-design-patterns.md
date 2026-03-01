# 游戏设计模式

游戏开发中常用的设计模式与架构。

## 目录

- [游戏架构模式](#游戏架构模式)
- [对象池模式](#对象池模式)
- [组件系统](#组件系统)
- [状态机](#状态机)
- [事件系统](#事件系统)

---

## 游戏架构模式

### Entity-Component-System (ECS)

```csharp
// Unity DOTS / 自定义ECS
public struct Position : IComponentData {
    public float3 Value;
}

public struct Velocity : IComponentData {
    public float3 Value;
}

public class MovementSystem : SystemBase {
    protected override void OnUpdate() {
        Entities
            .ForEach((ref Position pos, in Velocity vel) => {
                pos.Value += vel.Value * Time.DeltaTime;
            })
            .ScheduleParallel();
    }
}
```

### 游戏循环

```csharp
public class GameLoop {
    public void Run() {
        while(isRunning) {
            // 1. 处理输入
            ProcessInput();

            // 2. 更新逻辑
            Update(Time.deltaTime);

            // 3. 渲染
            Render();

            // 4. 帧率控制
            CapFrameRate();
        }
    }
}
```

---

## 对象池模式

```csharp
public class ObjectPool<T> where T : MonoBehaviour {
    private Queue<T> pool = new Queue<T>();
    private T prefab;

    public ObjectPool(T prefab, int initialSize) {
        this.prefab = prefab;
        for(int i = 0; i < initialSize; i++) {
            CreateObject();
        }
    }

    private void CreateObject() {
        T obj = Object.Instantiate(prefab);
        obj.gameObject.SetActive(false);
        pool.Enqueue(obj);
    }

    public T Get() {
        if(pool.Count == 0) CreateObject();
        T obj = pool.Dequeue();
        obj.gameObject.SetActive(true);
        return obj;
    }

    public void Return(T obj) {
        obj.gameObject.SetActive(false);
        pool.Enqueue(obj);
    }
}

// 使用
ObjectPool<Bullet> bulletPool = new ObjectPool<Bullet>(bulletPrefab, 50);
Bullet bullet = bulletPool.Get();
// ... 使用完毕 ...
bulletPool.Return(bullet);
```

---

## 组件系统

```csharp
// 游戏实体基类
public class GameEntity : MonoBehaviour {
    private Dictionary<Type, IComponent> components = new();

    public void AddComponent<T>(T component) where T : IComponent {
        components[typeof(T)] = component;
        component.Owner = this;
    }

    public T GetComponent<T>() where T : class, IComponent {
        return components.TryGetValue(typeof(T), out var comp) ? comp as T : null;
    }
}

// 组件接口
public interface IComponent {
    GameEntity Owner { get; set; }
    void Update(float deltaTime);
}

// 具体组件
public class HealthComponent : MonoBehaviour, IComponent {
    public GameEntity Owner { get; set; }
    public float MaxHealth { get; set; }
    public float CurrentHealth { get; set; }

    public void TakeDamage(float damage) {
        CurrentHealth -= damage;
        if(CurrentHealth <= 0) {
            Owner.GetComponent<DeathComponent>()?.Die();
        }
    }
}
```

---

## 状态机

```csharp
// 状态接口
public interface IState {
    void Enter();
    void Update(float deltaTime);
    void Exit();
}

// 具体状态
public class IdleState : IState {
    private Player player;

    public IdleState(Player player) {
        this.player = player;
    }

    public void Enter() {
        player.PlayAnimation("idle");
    }

    public void Update(float deltaTime) {
        if(Input.GetAxis("Horizontal") != 0) {
            player.ChangeState(new WalkState(player));
        }
        if(Input.GetButtonDown("Jump")) {
            player.ChangeState(new JumpState(player));
        }
    }

    public void Exit() {}
}

// 状态机
public class StateMachine {
    private IState currentState;

    public void ChangeState(IState newState) {
        currentState?.Exit();
        currentState = newState;
        currentState.Enter();
    }

    public void Update(float deltaTime) {
        currentState?.Update(deltaTime);
    }
}
```

---

## 事件系统

```csharp
// 全局事件系统
public static class GameEvents {
    public static Action OnPlayerDeath;
    public static Action<int> OnScoreChanged;
    public static Action<float> OnHealthChanged;

    // 带参数的事件
    public static void TriggerPlayerDeath() => OnPlayerDeath?.Invoke();
    public static void TriggerScoreChanged(int score) => OnScoreChanged?.Invoke(score);
}

// 使用
public class UIManager : MonoBehaviour {
    void OnEnable() {
        GameEvents.OnScoreChanged += UpdateScoreUI;
        GameEvents.OnHealthChanged += UpdateHealthUI;
    }

    void OnDisable() {
        GameEvents.OnScoreChanged -= UpdateScoreUI;
        GameEvents.OnHealthChanged -= UpdateHealthUI;
    }

    void UpdateScoreUI(int score) {
        scoreText.text = $"Score: {score}";
    }
}
```

---

## 检查清单

- [ ] 是否使用了对象池避免GC？
- [ ] 游戏循环是否符合固定时间步长？
- [ ] 状态机转换是否清晰？
- [ ] 事件是否正确注销避免内存泄漏？
- [ ] 物理更新是否在FixedUpdate中？
