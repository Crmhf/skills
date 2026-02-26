# PR（比例谐振）控制器设计理论

## 1. 控制器原理

PR控制器是交流系统中替代PI控制器的理想选择，可在静止坐标系下实现无静差跟踪。

### 1.1 理想PR控制器

**连续域传递函数**：
```
G_PR(s) = Kp + Kr * s / (s² + ω₀²)
```

其中：
- `Kp`：比例增益，影响响应速度
- `Kr`：谐振增益，影响稳态精度
- `ω₀`：谐振角频率（rad/s），如50Hz对应314.16 rad/s

**特性**：在 `ω = ω₀` 处提供无穷大增益，实现正弦参考信号的无静差跟踪。

### 1.2 准PR控制器（实际实现）

理想PR无法实现，采用带截止频率的准PR：
```
G_QPR(s) = Kp + Kr * (2ωc * s) / (s² + 2ωc * s + ω₀²)
```

其中新增：
- `ωc`：截止频率（rad/s），决定谐振峰宽度，典型值5-15 rad/s

**频率响应特性**：
- 带宽 ≈ `ωc/π` (Hz)
- `ωc` 越大：带宽越宽，对频率偏移鲁棒性越好，但谐波抑制能力下降
- `ωc` 越小：选择性越好，但对电网频率波动敏感

## 2. 离散化方法

### 2.1 双线性变换（Tustin）

最常用的离散化方法，保持稳定性：
```
s = (2/Ts) * (z-1)/(z+1)
```

**准PR的离散形式**：
```c
/* 差分方程系数计算 */
void PR_CalculateCoefficients(PR_Controller_t *ctrl) {
    float32_t Ts = ctrl->Ts;
    float32_t w0 = ctrl->w0;
    float32_t wc = ctrl->wc;

    /* 双线性变换参数 */
    float32_t c1 = 4.0f * wc / Ts;
    float32_t c2 = 4.0f / (Ts * Ts);
    float32_t w0_sq = w0 * w0;

    float32_t denom = c2 + 2.0f * wc / Ts * 2.0f + w0_sq;

    /* 分子系数 (b0, b1, b2) */
    ctrl->b[0] = (c1 + c2) / denom;
    ctrl->b[1] = (-2.0f * c2 + 2.0f * w0_sq) / denom;  /* 实际实现需调整 */
    ctrl->b[2] = (-c1 + c2) / denom;

    /* 分母系数 (a0=1, a1, a2) */
    ctrl->a[1] = (2.0f * c2 - 2.0f * w0_sq) / denom;
    ctrl->a[2] = (-c2 + 2.0f * wc / Ts * 2.0f - w0_sq) / denom;
}
```

### 2.2 预畸变双线性变换

在谐振频率处保持精确频率响应：
```
ω₀' = (2/Ts) * tan(ω₀ * Ts / 2)
```

用 `ω₀'` 代替 `ω₀` 进行双线性变换。

### 2.3 直接II型实现（推荐）

```c
float32_t PR_Controller_Update(PR_Controller_t *ctrl,
                               float32_t ref,
                               float32_t feedback) {
    float32_t error = ref - feedback;

    /* 谐振部分（直接II型）*/
    float32_t w = error - ctrl->a[1] * ctrl->x[0] - ctrl->a[2] * ctrl->x[1];
    float32_t y_res = ctrl->b[0] * w + ctrl->b[1] * ctrl->x[0] + ctrl->b[2] * ctrl->x[1];

    /* 更新状态 */
    ctrl->x[1] = ctrl->x[0];
    ctrl->x[0] = w;

    /* 比例 + 谐振 */
    float32_t output = ctrl->Kp * error + ctrl->Kr * y_res;

    /* 输出限幅 */
    if (output > ctrl->u_max) output = ctrl->u_max;
    if (output < ctrl->u_min) output = ctrl->u_min;

    return output;
}
```

## 3. 参数整定方法

### 3.1 基于穿越频率的整定

**设计目标**：
- 穿越频率 `fc`：电流环典型值 500~2000 Hz
- 相位裕度 `PM`：>45°

**整定步骤**：
```c
void PR_AutoTune(PR_Controller_t *ctrl,
                 float32_t L,      /* 滤波电感 (H) */
                 float32_t R,      /* 等效电阻 (Ω) */
                 float32_t fc,     /* 目标穿越频率 (Hz) */
                 float32_t Vdc) {  /* 直流母线电压 (V) */

    float32_t wc = 2.0f * PI * fc;
    float32_t w0 = ctrl->w0;  /* 基波角频率 */

    /* Kp基于电感电流环带宽 */
    ctrl->Kp = 2.0f * PI * fc * L / Vdc;

    /* Kr影响低频增益，通常 Kp:Kr ≈ 1:10 ~ 1:50 */
    ctrl->Kr = 20.0f * ctrl->Kp;

    /* wc选择：典型值 5~15 rad/s (0.8~2.5 Hz带宽) */
    ctrl->wc = 10.0f;
}
```

### 3.2 典型参数参考

| 应用场景 | Kp | Kr | ωc (rad/s) | Ts (μs) |
|----------|-----|-----|------------|---------|
| 单相逆变器 (50Hz) | 0.5~2.0 | 10~50 | 5~10 | 50~100 |
| 三相并网逆变器 | 0.3~1.5 | 10~40 | 8~15 | 50~100 |
| 高频链逆变器 | 0.1~0.5 | 5~20 | 10~20 | 20~50 |

## 4. 多谐振PR控制器

为抑制特定次谐波，可并联多个谐振项：
```
G_MRPR(s) = Kp + Σ Kr_i * (2ωc_i * s) / (s² + 2ωc_i * s + ω_i²)
```

**典型应用**：抑制3、5、7次谐波
```c
typedef struct {
    PR_Controller_t base;       /* 基波PR */
    PR_Controller_t harmonic[3]; /* 3/5/7次谐波PR */
} MRPR_Controller_t;

float32_t MRPR_Update(MRPR_Controller_t *ctrl, float32_t ref, float32_t feedback) {
    float32_t output = PR_Controller_Update(&ctrl->base, ref, feedback);

    /* 各谐波控制器只使用谐振部分（不含比例项）*/
    for (int i = 0; i < 3; i++) {
        float32_t err = ref - feedback;
        output += ctrl->harmonic[i].Kr * PR_ResonantPart(&ctrl->harmonic[i], err);
    }

    return output;
}
```

## 5. 数值稳定性考虑

### 5.1 离散化误差

- 高采样率（>20kHz）：双线性变换足够精确
- 低采样率：考虑零阶保持（ZOH）或预畸变

### 5.2 系数量化

定点实现时，系数需Q格式量化：
```c
/* Q30格式系数 */
#define Q30 1073741824.0f

int32_t b0_q30 = (int32_t)(b0 * Q30);
int32_t b1_q30 = (int32_t)(b1 * Q30);

/* 定点乘法（需64位中间结果防止溢出）*/
int64_t temp = (int64_t)b0_q30 * (int64_t)w_q15;
int32_t y_q15 = (int32_t)(temp >> 30);
```

### 5.3 积分饱和处理

```c
/* 条件积分法 */
if ((output >= ctrl->u_max && error > 0) ||
    (output <= ctrl->u_min && error < 0)) {
    /* 饱和时停止积分 */
} else {
    ctrl->x[0] = w;  /* 正常积分 */
}
```

## 6. 性能验证

### 6.1 频率响应测试

```c
/* 注入扫频信号，测量闭环响应 */
void PR_FrequencyResponseTest(PR_Controller_t *ctrl) {
    for (float32_t f = 10.0f; f < 5000.0f; f *= 1.1f) {
        float32_t omega = 2.0f * PI * f;
        /* 注入正弦，测量输出幅值/相位 */
        /* ... */
    }
}
```

### 6.2 阶跃响应测试

```c
/* 参考电流阶跃变化，观察响应时间/超调 */
void PR_StepResponseTest(void) {
    float32_t ref_step = 10.0f;  /* 10A阶跃 */
    uint32_t step_time_us = measure_settling_time(ref_step);
    float32_t overshoot = measure_overshoot();
}
```

## 参考资料

1. T. Noguchi et al., "Direct Power Control of PWM Converter Without Power-Source Voltage Sensors"
2. M. Castilla et al., "Reduction of Current Harmonic Distortion in Three-Phase Grid-Connected Photovoltaic Inverters"
3. R. Teodorescu et al., "Proportional-Resistant Controllers and Filters for Grid-Connected Voltage-Source Converters"
