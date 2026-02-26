# SVPWM（空间矢量脉宽调制）实现指南

## 1. 基本原理

### 1.1 电压空间矢量

三相逆变器8个开关状态对应8个基本电压矢量：
- **6个有效矢量**（V1~V6）：形成六边形边界
- **2个零矢量**（V0, V7）：位于中心

```
        V4(100)        V6(101)
           \          /
            \   S1   /
             \______/
         S6 /        \ S2
    V5(110)/    S0    \V1(001)
           \  (V0/V7) /
            \________/
           /   S3    \
         /            \
       V3(011)        V2(010)
```

### 1.2 矢量合成

任意参考电压 `Vref` 可由所在扇区的两个相邻基本矢量和零矢量合成：
```
Vref * Ts = T1 * Vn + T2 * V(n+1) + T0 * Vzero

其中：Ts = T1 + T2 + T0 （PWM周期）
```

## 2. 七段式SVPWM实现

### 2.1 扇区判断

基于 `Vα` 和 `Vβ` 判断所在扇区：

```c
uint8_t SVPWM_GetSector(float32_t v_alpha, float32_t v_beta) {
    float32_t u1 = v_beta;
    float32_t u2 = 0.866025f * v_alpha - 0.5f * v_beta;
    float32_t u3 = -0.866025f * v_alpha - 0.5f * v_beta;

    uint8_t sector = 0;
    if (u1 > 0) sector |= 1;
    if (u2 > 0) sector |= 2;
    if (u3 > 0) sector |= 4;

    return sector;  /* 1~6对应扇区I~VI，0为无效 */
}
```

### 2.2 作用时间计算

```c
typedef struct {
    float32_t ta, tb, tc;   /* 三相导通时间 */
    uint8_t sector;         /* 扇区号 */
} SVPWM_Result_t;

void SVPWM_Calculate(float32_t v_alpha, float32_t v_beta,
                     float32_t vdc, float32_t tpwm,
                     SVPWM_Result_t *result) {
    /* 归一化到Vdc */
    float32_t valpha_norm = v_alpha / vdc;
    float32_t vbeta_norm = v_beta / vdc;

    /* 中间变量 */
    float32_t X = vbeta_norm;
    float32_t Y = 0.866025f * valpha_norm + 0.5f * vbeta_norm;
    float32_t Z = -0.866025f * valpha_norm + 0.5f * vbeta_norm;

    /* 扇区判断 */
    uint8_t sector = SVPWM_GetSector(valpha_norm, vbeta_norm);
    result->sector = sector;

    float32_t t1, t2;
    switch (sector) {
        case 1: t1 = -Z; t2 = -X; break;
        case 2: t1 = Z;  t2 = Y;  break;
        case 3: t1 = X;  t2 = -Y; break;
        case 4: t1 = -X; t2 = Z;  break;
        case 5: t1 = -Y; t2 = -Z; break;
        case 6: t1 = Y;  t2 = X;  break;
        default: t1 = t2 = 0; break;
    }

    /* 过调制处理 */
    float32_t sum = t1 + t2;
    if (sum > 1.0f) {
        t1 = t1 / sum;
        t2 = t2 / sum;
    }

    float32_t t0 = 1.0f - t1 - t2;  /* 零矢量时间 */

    /* 七段式SVPWM：V0 - Vn - V(n+1) - V7 - V(n+1) - Vn - V0 */
    switch (sector) {
        case 1: /* V0-V1-V2-V7-V2-V1-V0 */
            result->ta = 0.25f * t0;
            result->tb = 0.25f * t0 + 0.5f * t1;
            result->tc = 0.25f * t0 + 0.5f * t1 + 0.5f * t2;
            break;
        case 2: /* V0-V3-V2-V7-V2-V3-V0 */
            result->ta = 0.25f * t0 + 0.5f * t2;
            result->tb = 0.25f * t0;
            result->tc = 0.25f * t0 + 0.5f * t1 + 0.5f * t2;
            break;
        case 3: /* V0-V3-V4-V7-V4-V3-V0 */
            result->ta = 0.25f * t0 + 0.5f * t1 + 0.5f * t2;
            result->tb = 0.25f * t0;
            result->tc = 0.25f * t0 + 0.5f * t1;
            break;
        case 4: /* V0-V5-V4-V7-V4-V5-V0 */
            result->ta = 0.25f * t0 + 0.5f * t1 + 0.5f * t2;
            result->tb = 0.25f * t0 + 0.5f * t2;
            result->tc = 0.25f * t0;
            break;
        case 5: /* V0-V5-V6-V7-V6-V5-V0 */
            result->ta = 0.25f * t0 + 0.5f * t1;
            result->tb = 0.25f * t0 + 0.5f * t1 + 0.5f * t2;
            result->tc = 0.25f * t0;
            break;
        case 6: /* V0-V1-V6-V7-V6-V1-V0 */
            result->ta = 0.25f * t0;
            result->tb = 0.25f * t0 + 0.5f * t1 + 0.5f * t2;
            result->tc = 0.25f * t0 + 0.5f * t2;
            break;
        default:
            result->ta = result->tb = result->tc = 0.25f;
            break;
    }

    /* 转换为实际时间 */
    result->ta *= tpwm;
    result->tb *= tpwm;
    result->tc *= tpwm;
}
```

## 3. 过调制策略

### 3.1 过调制分类

| 区域 | 条件 | 策略 |
|------|------|------|
| **线性区** | \|Vref\| ≤ Vdc/√3 | 标准SVPWM |
| **过调制I区** | Vdc/√3 < \|Vref\| < 2Vdc/3 | 角度保持，幅值限制 |
| **过调制II区** | \|Vref\| ≥ 2Vdc/3 | 六步方波逼近 |

### 3.2 最小幅值限制过调制

```c
void SVPWM_OverModulation(float32_t *v_alpha, float32_t *v_beta,
                          float32_t vdc, uint8_t mode) {
    float32_t v_max = vdc / SQRT3;  /* 线性区最大电压 */
    float32_t v_mag = sqrtf(*v_alpha * *v_alpha + *v_beta * *v_beta);

    if (mode == 1 && v_mag > v_max) {
        /* 过调制I区：保持角度，限制幅值 */
        float32_t scale = v_max / v_mag;
        *v_alpha *= scale;
        *v_beta *= scale;
    } else if (mode == 2 && v_mag > 2.0f * vdc / 3.0f) {
        /* 过调制II区：六步方波 */
        float32_t angle = atan2f(*v_beta, *v_alpha);
        float32_t sector_angle = fmodf(angle, PI / 3.0f);

        /* 将参考矢量拉向最近的六个顶点 */
        if (sector_angle < PI / 6.0f) {
            *v_alpha = 2.0f * vdc / 3.0f * cosf(angle - sector_angle);
            *v_beta = 2.0f * vdc / 3.0f * sinf(angle - sector_angle);
        } else {
            *v_alpha = 2.0f * vdc / 3.0f * cosf(angle + PI/3.0f - sector_angle);
            *v_beta = 2.0f * vdc / 3.0f * sinf(angle + PI/3.0f - sector_angle);
        }
    }
}
```

## 4. 计算优化

### 4.1 查表法三角函数

```c
/* 256点正弦查表 */
#define SIN_TABLE_SIZE 256

const q15_t sin_table[SIN_TABLE_SIZE + 1] = {
    /* 预计算 sin(2π * i / 256) * 32767 */
    0, 804, 1607, 2410, ...
};

float32_t fast_sin(float32_t angle) {
    /* 将角度映射到 0~2π */
    while (angle < 0) angle += PI2;
    while (angle >= PI2) angle -= PI2;

    /* 查表索引 */
    float32_t norm_angle = angle / PI2;  /* 0~1 */
    uint16_t index = (uint16_t)(norm_angle * SIN_TABLE_SIZE);

    /* 线性插值 */
    float32_t frac = norm_angle * SIN_TABLE_SIZE - index;
    q15_t y1 = sin_table[index];
    q15_t y2 = sin_table[index + 1];

    return F32_FROM_Q15(y1 + (q15_t)(frac * (y2 - y1)));
}
```

### 4.2 无除法实现

```c
/* 快速近似 1/sqrt(x) */
float32_t fast_inv_sqrt(float32_t x) {
    union {
        float32_t f;
        int32_t i;
    } conv;

    float32_t xhalf = 0.5f * x;
    conv.f = x;
    conv.i = 0x5f3759df - (conv.i >> 1);  /* 魔法数字 */
    conv.f = conv.f * (1.5f - xhalf * conv.f * conv.f);  /* Newton迭代 */
    return conv.f;
}
```

## 5. 死区补偿

```c
typedef struct {
    float32_t dead_time;        /* 死区时间 (s) */
    float32_t v_dc;             /* 直流母线电压 */
    float32_t i_threshold;      /* 电流阈值 */
    float32_t compensation_gain;/* 补偿增益 */
} DeadTime_Compensator_t;

float32_t DeadTime_Compensate(DeadTime_Compensator_t *comp,
                              float32_t duty_cmd,
                              float32_t i_phase) {
    /* 根据电流方向补偿死区 */
    float32_t compensation = 0.0f;

    if (ABS(i_phase) > comp->i_threshold) {
        /* 补偿量 = 死区时间 / PWM周期 */
        float32_t comp_duty = comp->dead_time * comp->compensation_gain;

        if (i_phase > 0) {
            /* 电流流出：实际导通时间比指令短 */
            compensation = comp_duty;
        } else {
            /* 电流流入：实际导通时间比指令长 */
            compensation = -comp_duty;
        }
    }

    return SATURATE(duty_cmd + compensation, 0.0f, 1.0f);
}
```

## 6. 开关损耗优化

### 6.1 不连续PWM（DPWM）

在轻载时减少开关次数：
```c
void DPWM_Calculate(float32_t v_alpha, float32_t v_beta,
                    float32_t vdc, float32_t i_alpha, float32_t i_beta,
                    SVPWM_Result_t *result) {
    /* 标准SVPWM计算 */
    SVPWM_Calculate(v_alpha, v_beta, vdc, 1.0f, result);

    /* 根据电流矢量位置选择钳位相 */
    float32_t i_angle = atan2f(i_beta, i_alpha);
    uint8_t clamp_sector = (uint8_t)((i_angle + PI/6.0f) / (PI/3.0f)) % 6;

    /* 将最大相或最小相钳位到0或1，减少开关次数 */
    switch (clamp_sector) {
        case 0: /* A相钳位到1（上管常开）*/
            result->ta = 1.0f;
            break;
        case 3: /* A相钳位到0（下管常开）*/
            result->ta = 0.0f;
            break;
        /* ... 其他相类似处理 */
    }
}
```
