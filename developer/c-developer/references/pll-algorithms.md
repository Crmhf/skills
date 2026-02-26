# 锁相环（PLL）算法实现

## 1. SRF-PLL（同步参考坐标系锁相环）

### 1.1 原理

将电网电压变换到旋转dq坐标系，通过控制Vq=0实现锁相。

```
Vα = Va
Vβ = (Va + 2Vb) / √3

Vd =  Vα·cos(θ) + Vβ·sin(θ)
Vq = -Vα·sin(θ) + Vβ·cos(θ)

目标：Vq → 0（说明θ与电网电压同步）
```

### 1.2 标准实现

```c
#ifndef SRF_PLL_H
#define SRF_PLL_H

#include "types.h"

typedef struct {
    /* PI参数 */
    float32_t Kp;
    float32_t Ki;

    /* 前馈 */
    float32_t w_ff;         /* 前馈角频率（如314.16 rad/s对应50Hz）*/

    /* 限幅 */
    float32_t w_max;        /* 最大角频率 */
    float32_t w_min;        /* 最小角频率 */

    /* 状态 */
    float32_t theta;        /* 输出相位角 [0, 2π) */
    float32_t omega;        /* 输出角频率 */
    float32_t integrator;   /* PI积分器 */

    /* 输出 */
    float32_t vd;           /* d轴电压（用于幅值监测）*/
    float32_t vq;           /* q轴电压（用于锁相误差）*/
    bool locked;            /* 锁定状态 */
    uint16_t lock_counter;  /* 锁定计数器 */
} SRF_PLL_t;

void SRF_PLL_Init(SRF_PLL_t *pll, float32_t Kp, float32_t Ki,
                  float32_t w_ff, float32_t w_max, float32_t w_min);
void SRF_PLL_Update(SRF_PLL_t *pll, float32_t v_alpha, float32_t v_beta);
void SRF_PLL_Reset(SRF_PLL_t *pll);
bool SRF_PLL_IsLocked(SRF_PLL_t *pll);

#endif /* SRF_PLL_H */
```

```c
/* srf_pll.c */
#include "srf_pll.h"

#define LOCK_THRESHOLD  0.05f   /* Vq锁定阈值 */
#define LOCK_COUNT      100     /* 连续满足阈值计数 */

void SRF_PLL_Init(SRF_PLL_t *pll, float32_t Kp, float32_t Ki,
                  float32_t w_ff, float32_t w_max, float32_t w_min) {
    pll->Kp = Kp;
    pll->Ki = Ki;
    pll->w_ff = w_ff;
    pll->w_max = w_max;
    pll->w_min = w_min;
    SRF_PLL_Reset(pll);
}

void SRF_PLL_Reset(SRF_PLL_t *pll) {
    pll->theta = 0.0f;
    pll->omega = pll->w_ff;
    pll->integrator = 0.0f;
    pll->vd = 0.0f;
    pll->vq = 0.0f;
    pll->locked = false;
    pll->lock_counter = 0;
}

void SRF_PLL_Update(SRF_PLL_t *pll, float32_t v_alpha, float32_t v_beta) {
    /* Park变换 */
    float32_t cos_theta = cosf(pll->theta);
    float32_t sin_theta = sinf(pll->theta);

    pll->vd =  v_alpha * cos_theta + v_beta * sin_theta;
    pll->vq = -v_alpha * sin_theta + v_beta * cos_theta;

    /* 相位误差（Vq应为0）*/
    float32_t error = -pll->vq;

    /* PI控制器 */
    pll->integrator += pll->Ki * error;
    pll->integrator = SATURATE(pll->integrator,
                                  pll->w_min - pll->w_ff,
                                  pll->w_max - pll->w_ff);

    pll->omega = pll->w_ff + pll->Kp * error + pll->integrator;
    pll->omega = SATURATE(pll->omega, pll->w_min, pll->w_max);

    /* 角度积分 */
    pll->theta += pll->omega * SAMPLING_PERIOD;

    /* 角度归一化到 [0, 2π) */
    while (pll->theta >= PI2) pll->theta -= PI2;
    while (pll->theta < 0.0f) pll->theta += PI2;

    /* 锁定检测 */
    if (ABS(pll->vq) < LOCK_THRESHOLD) {
        if (pll->lock_counter < LOCK_COUNT) {
            pll->lock_counter++;
        } else {
            pll->locked = true;
        }
    } else {
        pll->lock_counter = 0;
        pll->locked = false;
    }
}

bool SRF_PLL_IsLocked(SRF_PLL_t *pll) {
    return pll->locked;
}
```

### 1.3 参数整定

```c
void SRF_PLL_AutoTune(SRF_PLL_t *pll, float32_t bandwidth_hz) {
    /* 基于带宽的整定
     * 开环传递函数：G(s) = Vd * (Kp + Ki/s) / s
     * 典型二阶系统形式
     */
    float32_t wn = 2.0f * PI * bandwidth_hz;  /* 自然频率 */

    /* 阻尼比 ζ = 0.707（最佳响应）*/
    float32_t zeta = 0.707f;

    /* 假设Vd标幺值为1 */
    float32_t Vd = 1.0f;

    pll->Kp = 2.0f * zeta * wn / Vd;
    pll->Ki = (wn * wn) / Vd;
}
```

## 2. DDSRF-PLL（双dq同步参考坐标系锁相环）

### 2.1 原理

用于不平衡电网条件，分离正序和负序分量。

```c
typedef struct {
    /* 正序PLL */
    float32_t Kp_pos, Ki_pos;
    float32_t theta_pos;
    float32_t omega_pos;
    float32_t vd_pos, vq_pos;

    /* 负序PLL */
    float32_t Kp_neg, Ki_neg;
    float32_t theta_neg;
    float32_t omega_neg;
    float32_t vd_neg, vq_neg;

    /* 前馈 */
    float32_t w_ff;

    /* 低通滤波器（用于序分量分离）*/
    float32_t lp_alpha;     /* LPF系数: 0.1~0.3 */

    /* 内部状态 */
    float32_t d1_pos, q1_pos;   /* 正序中间变量 */
    float32_t d2_pos, q2_pos;
    float32_t d1_neg, q1_neg;   /* 负序中间变量 */
    float32_t d2_neg, q2_neg;
} DDSRF_PLL_t;
```

### 2.2 实现

```c
void DDSRF_PLL_Update(DDSRF_PLL_t *pll, float32_t v_alpha, float32_t v_beta) {
    /* 正序旋转坐标系变换 */
    float32_t cos_pos = cosf(pll->theta_pos);
    float32_t sin_pos = sinf(pll->theta_pos);

    float32_t v_d1_pos =  v_alpha * cos_pos + v_beta * sin_pos;
    float32_t v_q1_pos = -v_alpha * sin_pos + v_beta * cos_pos;

    /* 负序旋转坐标系变换（反向旋转）*/
    float32_t cos_neg = cosf(-pll->theta_neg);
    float32_t sin_neg = sinf(-pll->theta_neg);

    float32_t v_d1_neg =  v_alpha * cos_neg + v_beta * sin_neg;
    float32_t v_q1_neg = -v_alpha * sin_neg + v_beta * cos_neg;

    /* 低通滤波分离序分量 */
    pll->d1_pos += pll->lp_alpha * (v_d1_pos - pll->d2_neg - pll->d1_pos);
    pll->q1_pos += pll->lp_alpha * (v_q1_pos - pll->q2_neg - pll->q1_pos);

    pll->d1_neg += pll->lp_alpha * (v_d1_neg - pll->d2_pos - pll->d1_neg);
    pll->q1_neg += pll->lp_alpha * (v_q1_neg - pll->q2_pos - pll->q1_neg);

    pll->d2_pos = pll->d1_pos;
    pll->q2_pos = pll->q1_pos;
    pll->d2_neg = pll->d1_neg;
    pll->q2_neg = pll->q1_neg;

    /* 正序PLL控制 */
    pll->vd_pos = pll->d1_pos;
    pll->vq_pos = pll->q1_pos;

    float32_t error_pos = -pll->vq_pos;
    pll->omega_pos = pll->w_ff + pll->Kp_pos * error_pos;
    pll->theta_pos += pll->omega_pos * SAMPLING_PERIOD;

    /* 负序PLL控制 */
    pll->vd_neg = pll->d1_neg;
    pll->vq_neg = pll->q1_neg;

    float32_t error_neg = -pll->vq_neg;
    pll->omega_neg = pll->w_ff + pll->Kp_neg * error_neg;
    pll->theta_neg += pll->omega_neg * SAMPLING_PERIOD;

    /* 角度归一化 */
    while (pll->theta_pos >= PI2) pll->theta_pos -= PI2;
    while (pll->theta_pos < 0.0f) pll->theta_pos += PI2;
    while (pll->theta_neg >= PI2) pll->theta_neg -= PI2;
    while (pll->theta_neg < 0.0f) pll->theta_neg += PI2;
}
```

## 3. SOGI-PLL（二阶广义积分器锁相环）

### 3.1 原理

使用SOGI生成正交信号，无需Clarke变换。

```c
typedef struct {
    /* SOGI参数 */
    float32_t K;            /* SOGI增益，典型值1.414（临界阻尼）*/
    float32_t w0;           /* 谐振频率 */

    /* SOGI状态 */
    float32_t u_alpha;      /* α轴输出（同相）*/
    float32_t u_beta;       /* β轴输出（正交）*/
    float32_t x1, x2;       /* 内部状态 */

    /* PLL部分 */
    float32_t Kp, Ki;
    float32_t theta;
    float32_t omega;
    float32_t integrator;

    /* 自适应频率 */
    bool adaptive;          /* 是否启用频率自适应 */
} SOGI_PLL_t;
```

### 3.2 实现

```c
void SOGI_PLL_Update(SOGI_PLL_t *pll, float32_t input) {
    /* SOGI自适应系数 */
    float32_t K = pll->K;
    float32_t w0 = pll->adaptive ? pll->omega : pll->w0;

    /* SOGI离散实现（双线性变换）*/
    float32_t error = input - pll->u_alpha;
    float32_t x1_new = pll->x1 + SAMPLING_PERIOD * (K * w0 * error - w0 * pll->x2);
    float32_t x2_new = pll->x2 + SAMPLING_PERIOD * (w0 * pll->x1);

    pll->x1 = x1_new;
    pll->x2 = x2_new;

    pll->u_alpha = x1_new;    /* 同相输出 */
    pll->u_beta = x2_new;     /* 正交输出（滞后90°）*/

    /* 后续PLL与SRF-PLL相同 */
    float32_t cos_theta = cosf(pll->theta);
    float32_t sin_theta = sinf(pll->theta);

    float32_t vq = -pll->u_alpha * sin_theta + pll->u_beta * cos_theta;

    pll->integrator += pll->Ki * (-vq);
    pll->omega = w0 + pll->Kp * (-vq) + pll->integrator;

    pll->theta += pll->omega * SAMPLING_PERIOD;

    while (pll->theta >= PI2) pll->theta -= PI2;
    while (pll->theta < 0.0f) pll->theta += PI2;
}
```

## 4. PLL性能对比

| 特性 | SRF-PLL | DDSRF-PLL | SOGI-PLL |
|------|---------|-----------|----------|
| **复杂度** | 低 | 高 | 中 |
| **不平衡电网** | 差 | 优 | 良 |
| **谐波抑制** | 差 | 差 | 优 |
| **频率自适应** | 需额外设计 | 需额外设计 | 内置 |
| **响应速度** | 快 | 中 | 中 |
| **适用场景** | 理想电网 | 严重不平衡 | 谐波污染 |

## 5. 频率自适应

```c
/* 频率自适应SRF-PLL */
typedef struct {
    SRF_PLL_t base;
    float32_t freq_nominal;     /* 额定频率 */
    float32_t freq_max;         /* 最大频率 */
    float32_t freq_min;         /* 最小频率 */
    float32_t freq_estimate;    /* 频率估计值 */
} Adaptive_SRF_PLL_t;

void Adaptive_SRF_PLL_Update(Adaptive_SRF_PLL_t *pll,
                             float32_t v_alpha, float32_t v_beta) {
    /* 标准SRF-PLL更新 */
    SRF_PLL_Update(&pll->base, v_alpha, v_beta);

    /* 频率估计 */
    pll->freq_estimate = pll->base.omega / (2.0f * PI);

    /* 限幅 */
    pll->freq_estimate = SATURATE(pll->freq_estimate,
                                   pll->freq_min, pll->freq_max);

    /* 更新前馈频率（慢速跟踪）*/
    float32_t alpha = 0.01f;  /* 跟踪系数 */
    pll->base.w_ff += alpha * (pll->freq_estimate * 2.0f * PI - pll->base.w_ff);
}
```
