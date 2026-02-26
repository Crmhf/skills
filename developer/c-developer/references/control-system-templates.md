# 电力电子控制系统代码模板

## 1. 数据类型定义 (types.h)

```c
#ifndef TYPES_H
#define TYPES_H

#include <stdint.h>
#include <stdbool.h>

/* 浮点类型 */
typedef float   float32_t;
typedef double  float64_t;

/* 定点数类型 */
typedef int16_t q15_t;
typedef int32_t q31_t;
typedef int64_t q63_t;

/* 数值常量 */
#define PI          3.14159265358979323846f
#define PI2         (2.0f * PI)
#define PI_HALF     (PI / 2.0f)
#define SQRT3       1.7320508075688772f
#define INV_SQRT3   (1.0f / SQRT3)
#define SQRT2       1.4142135623730951f

/* 限幅宏 */
#define SATURATE(x, min, max)   ((x) > (max) ? (max) : ((x) < (min) ? (min) : (x)))
#define ABS(x)                  ((x) >= 0 ? (x) : -(x))
#define SIGN(x)                 ((x) >= 0 ? 1 : -1)

/* Q格式转换 */
#define Q15(x)      ((q15_t)((x) * 32768.0f))
#define Q31(x)      ((q31_t)((x) * 2147483648.0f))
#define F32_FROM_Q15(x) ((float32_t)(x) / 32768.0f)
#define F32_FROM_Q31(x) ((float32_t)(x) / 2147483648.0f)

#endif /* TYPES_H */
```

## 2. PI控制器模板

```c
#ifndef PI_CONTROLLER_H
#define PI_CONTROLLER_H

#include "types.h"

typedef struct {
    float32_t Kp;           /* 比例增益 */
    float32_t Ki;           /* 积分增益 */
    float32_t u_max;        /* 输出上限 */
    float32_t u_min;        /* 输出下限 */
    float32_t Ts;           /* 采样周期 */

    /* 内部状态 */
    float32_t integrator;   /* 积分器 */
    float32_t error_prev;   /* 上一拍误差（用于抗饱和）*/
    float32_t output;       /* 当前输出 */
} PI_Controller_t;

/* 函数声明 */
void PI_Init(PI_Controller_t *ctrl, float32_t Kp, float32_t Ki,
             float32_t u_max, float32_t u_min, float32_t Ts);
float32_t PI_Update(PI_Controller_t *ctrl, float32_t ref, float32_t feedback);
void PI_Reset(PI_Controller_t *ctrl);

#endif /* PI_CONTROLLER_H */
```

```c
/* pi_controller.c */
#include "pi_controller.h"

void PI_Init(PI_Controller_t *ctrl, float32_t Kp, float32_t Ki,
             float32_t u_max, float32_t u_min, float32_t Ts) {
    ctrl->Kp = Kp;
    ctrl->Ki = Ki;
    ctrl->u_max = u_max;
    ctrl->u_min = u_min;
    ctrl->Ts = Ts;
    PI_Reset(ctrl);
}

float32_t PI_Update(PI_Controller_t *ctrl, float32_t ref, float32_t feedback) {
    float32_t error = ref - feedback;

    /* 比例项 */
    float32_t P = ctrl->Kp * error;

    /* 积分项（带条件积分抗饱和）*/
    float32_t I_new = ctrl->integrator + ctrl->Ki * ctrl->Ts * error;

    /* 计算临时输出 */
    float32_t output = P + I_new;

    /* 输出限幅 + 条件积分 */
    if (output > ctrl->u_max) {
        output = ctrl->u_max;
        /* 只积分当误差趋向于减小输出时 */
        if (error < 0) {
            ctrl->integrator = I_new;
        }
    } else if (output < ctrl->u_min) {
        output = ctrl->u_min;
        if (error > 0) {
            ctrl->integrator = I_new;
        }
    } else {
        /* 未饱和，正常积分 */
        ctrl->integrator = I_new;
    }

    ctrl->error_prev = error;
    ctrl->output = output;
    return output;
}

void PI_Reset(PI_Controller_t *ctrl) {
    ctrl->integrator = 0.0f;
    ctrl->error_prev = 0.0f;
    ctrl->output = 0.0f;
}
```

## 3. PR控制器完整实现

```c
#ifndef PR_CONTROLLER_H
#define PR_CONTROLLER_H

#include "types.h"

typedef struct {
    /* 参数 */
    float32_t Kp;           /* 比例增益 */
    float32_t Kr;           /* 谐振增益 */
    float32_t wc;           /* 截止频率 */
    float32_t w0;           /* 谐振角频率 */
    float32_t Ts;           /* 采样周期 */
    float32_t u_max;        /* 输出上限 */
    float32_t u_min;        /* 输出下限 */

    /* 离散系数 */
    float32_t b0, b1, b2;   /* 谐振部分分子 */
    float32_t a1, a2;       /* 谐振部分分母（a0=1）*/

    /* 状态 */
    float32_t x[2];         /* 延迟单元状态 */
    float32_t output;       /* 当前输出 */
} PR_Controller_t;

void PR_Init(PR_Controller_t *ctrl, float32_t Kp, float32_t Kr,
             float32_t wc, float32_t w0, float32_t Ts,
             float32_t u_max, float32_t u_min);
float32_t PR_Update(PR_Controller_t *ctrl, float32_t ref, float32_t feedback);
void PR_Reset(PR_Controller_t *ctrl);
void PR_SetFrequency(PR_Controller_t *ctrl, float32_t w0);

#endif /* PR_CONTROLLER_H */
```

```c
/* pr_controller.c */
#include "pr_controller.h"

void PR_Init(PR_Controller_t *ctrl, float32_t Kp, float32_t Kr,
             float32_t wc, float32_t w0, float32_t Ts,
             float32_t u_max, float32_t u_min) {
    ctrl->Kp = Kp;
    ctrl->Kr = Kr;
    ctrl->wc = wc;
    ctrl->w0 = w0;
    ctrl->Ts = Ts;
    ctrl->u_max = u_max;
    ctrl->u_min = u_min;

    PR_Reset(ctrl);
    PR_SetFrequency(ctrl, w0);
}

void PR_SetFrequency(PR_Controller_t *ctrl, float32_t w0) {
    ctrl->w0 = w0;

    /* 预畸变双线性变换 */
    float32_t wd = (2.0f / ctrl->Ts) * tanf(w0 * ctrl->Ts / 2.0f);

    /* 准PR传递函数系数计算 */
    float32_t Ts = ctrl->Ts;
    float32_t wc = ctrl->wc;

    /* 连续域分子: 2*wc*s */
    /* 连续域分母: s^2 + 2*wc*s + wd^2 */

    float32_t c = 2.0f / Ts;  /* 双线性变换常数 */
    float32_t wd_sq = wd * wd;

    /* 离散化后的系数（双线性变换）*/
    float32_t denom = c * c + 2.0f * wc * c + wd_sq;

    ctrl->b0 = 2.0f * wc * c / denom;
    ctrl->b1 = 0.0f;  /* 准PR的分子只有s项，对称 */
    ctrl->b2 = -ctrl->b0;

    ctrl->a1 = (2.0f * wd_sq - 2.0f * c * c) / denom;
    ctrl->a2 = (c * c - 2.0f * wc * c + wd_sq) / denom;
}

float32_t PR_Update(PR_Controller_t *ctrl, float32_t ref, float32_t feedback) {
    float32_t error = ref - feedback;

    /* 比例部分 */
    float32_t up = ctrl->Kp * error;

    /* 谐振部分（直接II型实现）*/
    float32_t w = error - ctrl->a1 * ctrl->x[0] - ctrl->a2 * ctrl->x[1];
    float32_t ur = ctrl->Kr * (ctrl->b0 * w + ctrl->b1 * ctrl->x[0] + ctrl->b2 * ctrl->x[1]);

    /* 更新状态 */
    ctrl->x[1] = ctrl->x[0];
    ctrl->x[0] = w;

    /* 总输出 */
    float32_t output = up + ur;

    /* 限幅 */
    output = SATURATE(output, ctrl->u_min, ctrl->u_max);

    ctrl->output = output;
    return output;
}

void PR_Reset(PR_Controller_t *ctrl) {
    ctrl->x[0] = 0.0f;
    ctrl->x[1] = 0.0f;
    ctrl->output = 0.0f;
}
```

## 4. 坐标变换模板

```c
#ifndef TRANSFORMS_H
#define TRANSFORMS_H

#include "types.h"

typedef struct {
    float32_t alpha;
    float32_t beta;
} AlphaBeta_t;

typedef struct {
    float32_t d;
    float32_t q;
} DQ_t;

typedef struct {
    float32_t a;
    float32_t b;
    float32_t c;
} ABC_t;

/* Clarke变换（abc -> αβ）*/
static inline void Clarke_Transform(const ABC_t *abc, AlphaBeta_t *ab) {
    ab->alpha = 2.0f / 3.0f * (abc->a - 0.5f * abc->b - 0.5f * abc->c);
    ab->beta  = INV_SQRT3 * (abc->b - abc->c);
}

/* 反Clarke变换（αβ -> abc）*/
static inline void Inverse_Clarke(const AlphaBeta_t *ab, ABC_t *abc) {
    abc->a = ab->alpha;
    abc->b = -0.5f * ab->alpha + 0.5f * SQRT3 * ab->beta;
    abc->c = -0.5f * ab->alpha - 0.5f * SQRT3 * ab->beta;
}

/* Park变换（αβ -> dq）*/
static inline void Park_Transform(const AlphaBeta_t *ab, float32_t theta, DQ_t *dq) {
    float32_t cos_theta = cosf(theta);
    float32_t sin_theta = sinf(theta);

    dq->d = ab->alpha * cos_theta + ab->beta * sin_theta;
    dq->q = -ab->alpha * sin_theta + ab->beta * cos_theta;
}

/* 反Park变换（dq -> αβ）*/
static inline void Inverse_Park(const DQ_t *dq, float32_t theta, AlphaBeta_t *ab) {
    float32_t cos_theta = cosf(theta);
    float32_t sin_theta = sinf(theta);

    ab->alpha = dq->d * cos_theta - dq->q * sin_theta;
    ab->beta  = dq->d * sin_theta + dq->q * cos_theta;
}

#endif /* TRANSFORMS_H */
```

## 5. 故障保护模板

```c
#ifndef FAULT_PROTECTION_H
#define FAULT_PROTECTION_H

#include "types.h"

/* 故障码定义 */
typedef enum {
    FAULT_NONE = 0,
    FAULT_OVER_CURRENT = (1 << 0),
    FAULT_OVER_VOLTAGE = (1 << 1),
    FAULT_UNDER_VOLTAGE = (1 << 2),
    FAULT_OVER_TEMP = (1 << 3),
    FAULT_IGBT_FAULT = (1 << 4),
    FAULT_GRID_LOST = (1 << 5),
    FAULT_PLL_UNLOCK = (1 << 6),
} FaultCode_t;

/* 保护阈值 */
typedef struct {
    float32_t i_max;        /* 过流阈值 (A) */
    float32_t v_dc_max;     /* 过压阈值 (V) */
    float32_t v_dc_min;     /* 欠压阈值 (V) */
    float32_t temp_max;     /* 过温阈值 (°C) */
    uint16_t  debounce_ms;  /* 去抖时间 (ms) */
} Protection_Thresholds_t;

/* 保护管理器 */
typedef struct {
    Protection_Thresholds_t thresholds;
    FaultCode_t active_faults;
    FaultCode_t latched_faults;
    uint16_t debounce_counter[8];
    bool protection_triggered;
    void (*fault_callback)(FaultCode_t fault);
} Protection_Manager_t;

void Protection_Init(Protection_Manager_t *mgr,
                    const Protection_Thresholds_t *thresholds,
                    void (*callback)(FaultCode_t));
FaultCode_t Protection_Update(Protection_Manager_t *mgr,
                              float32_t i_abc[3],
                              float32_t v_dc,
                              float32_t temp);
void Protection_Clear(Protection_Manager_t *mgr);
bool Protection_IsSafe(Protection_Manager_t *mgr);

#endif /* FAULT_PROTECTION_H */
```

```c
/* fault_protection.c */
#include "fault_protection.h"

void Protection_Init(Protection_Manager_t *mgr,
                    const Protection_Thresholds_t *thresholds,
                    void (*callback)(FaultCode_t)) {
    mgr->thresholds = *thresholds;
    mgr->fault_callback = callback;
    mgr->active_faults = FAULT_NONE;
    mgr->latched_faults = FAULT_NONE;
    mgr->protection_triggered = false;

    for (int i = 0; i < 8; i++) {
        mgr->debounce_counter[i] = 0;
    }
}

FaultCode_t Protection_Update(Protection_Manager_t *mgr,
                              float32_t i_abc[3],
                              float32_t v_dc,
                              float32_t temp) {
    FaultCode_t new_faults = FAULT_NONE;

    /* 过流检测（三相瞬时最大值）*/
    float32_t i_max = 0.0f;
    for (int i = 0; i < 3; i++) {
        if (ABS(i_abc[i]) > i_max) {
            i_max = ABS(i_abc[i]);
        }
    }
    if (i_max > mgr->thresholds.i_max) {
        new_faults |= FAULT_OVER_CURRENT;
    }

    /* 直流过压检测 */
    if (v_dc > mgr->thresholds.v_dc_max) {
        new_faults |= FAULT_OVER_VOLTAGE;
    }

    /* 直流欠压检测 */
    if (v_dc < mgr->thresholds.v_dc_min) {
        new_faults |= FAULT_UNDER_VOLTAGE;
    }

    /* 过温检测 */
    if (temp > mgr->thresholds.temp_max) {
        new_faults |= FAULT_OVER_TEMP;
    }

    /* 去抖处理 */
    FaultCode_t confirmed_faults = FAULT_NONE;
    for (int i = 0; i < 8; i++) {
        if (new_faults & (1 << i)) {
            if (mgr->debounce_counter[i] < mgr->thresholds.debounce_ms) {
                mgr->debounce_counter[i]++;
            } else {
                confirmed_faults |= (1 << i);
            }
        } else {
            mgr->debounce_counter[i] = 0;
        }
    }

    /* 更新故障状态 */
    mgr->active_faults = confirmed_faults;
    mgr->latched_faults |= confirmed_faults;

    /* 故障触发回调 */
    if (confirmed_faults != FAULT_NONE && !mgr->protection_triggered) {
        mgr->protection_triggered = true;
        if (mgr->fault_callback) {
            mgr->fault_callback(confirmed_faults);
        }
    }

    return confirmed_faults;
}

void Protection_Clear(Protection_Manager_t *mgr) {
    mgr->active_faults = FAULT_NONE;
    mgr->latched_faults = FAULT_NONE;
    mgr->protection_triggered = false;
    for (int i = 0; i < 8; i++) {
        mgr->debounce_counter[i] = 0;
    }
}

bool Protection_IsSafe(Protection_Manager_t *mgr) {
    return (mgr->active_faults == FAULT_NONE);
}
```
