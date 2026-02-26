# 电力电子C语言编码规范（基于MISRA-C）

## 1. 通用规则

### 1.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 宏/常量 | 全大写+下划线 | `MAX_CURRENT_A`, `PWM_FREQUENCY_HZ` |
| 结构体类型 | PascalCase+_t | `PR_Controller_t`, `Inverter_Status_t` |
| 函数 | snake_case | `pr_controller_update()`, `svpwm_calculate()` |
| 变量 | snake_case | `current_alpha`, `duty_cycle_a` |
| 全局变量 | g_前缀 | `g_inverter_state`, `g_fault_flags` |
| 静态变量 | s_前缀 | `s_pll_integrator` |
| 指针 | p_前缀 | `p_config`, `p_data` |

### 1.2 类型使用

```c
/* 强制使用stdint.h类型，禁止裸char/short/int/long */
typedef int8_t    int8;
typedef int16_t   int16;
typedef int32_t   int32;
typedef uint8_t   uint8;
typedef uint16_t  uint16;
typedef uint32_t  uint32;

/* 浮点类型 */
typedef float     float32;
typedef double    float64;

/* 布尔类型 */
#include <stdbool.h>
```

### 1.3 数值常量后缀

```c
/* 浮点常量必须带f后缀 */
float32 Kp = 0.5f;      /* 正确 */
float32 Kr = 10.0f;     /* 正确 */

/* 禁止 */
float32 bad = 0.5;      /* 错误：隐式double */
```

## 2. 控制算法专用规范

### 2.1 控制器结构体

```c
/* 必须包含完整状态 */
typedef struct {
    /* 参数（初始化时设置）*/
    const float32 Kp;
    const float32 Ki;
    const float32 Ts;       /* 采样周期 */

    /* 运行状态 */
    float32 integrator;     /* 积分器状态 */
    float32 prev_error;     /* 上一拍误差 */
    float32 output;         /* 当前输出 */

    /* 限幅 */
    const float32 u_max;
    const float32 u_min;

    /* 诊断 */
    uint32 update_count;    /* 更新计数 */
    bool saturated;         /* 饱和标志 */
} PI_Controller_t;
```

### 2.2 除零保护

```c
/* 所有除法必须有保护 */
float32 Divide_Safe(float32 num, float32 den, float32 default_val) {
    const float32 EPSILON = 1e-6f;

    if (den > EPSILON || den < -EPSILON) {
        return num / den;
    }
    return default_val;
}

/* 使用示例 */
voltage = Divide_Safe(power, current, 0.0f);
```

### 2.3 数组访问边界检查

```c
/* 相位索引访问 */
#define PHASE_A 0u
#define PHASE_B 1u
#define PHASE_C 2u
#define NUM_PHASES 3u

float32 get_phase_current(const float32 currents[], uint8 phase) {
    if (phase < NUM_PHASES) {
        return currents[phase];
    }
    return 0.0f;  /* 安全默认值 */
}
```

## 3. 安全关键规则

### 3.1 故障处理模式

```c
typedef enum {
    FAULT_LEVEL_NONE = 0,       /* 无故障 */
    FAULT_LEVEL_WARNING,        /* 警告（记录）*/
    FAULT_LEVEL_DERATE,         /* 降额运行 */
    FAULT_LEVEL_STOP,           /* 停机保护 */
    FAULT_LEVEL_EMERGENCY       /* 紧急停机 */
} Fault_Level_t;

typedef struct {
    uint16 code;                /* 故障码 */
    Fault_Level_t level;        /* 级别 */
    uint32 timestamp_ms;        /* 时间戳 */
    float32 value;              /* 触发值 */
} Fault_Record_t;
```

### 3.2 看门狗与超时

```c
#define PWM_TIMEOUT_MS      10u
#define PLL_LOCK_TIMEOUT_MS 5000u

typedef struct {
    uint32 last_pwm_time;
    uint32 last_pll_lock_time;
    bool watchdog_triggered;
} Safety_Monitor_t;

void Safety_Check(Safety_Monitor_t *mon, uint32 current_time) {
    /* PWM中断超时检测 */
    if ((current_time - mon->last_pwm_time) > PWM_TIMEOUT_MS) {
        Fault_Report(FAULT_PWM_LOST, FAULT_LEVEL_EMERGENCY);
    }

    /* PLL失锁超时 */
    if (!PLL_IsLocked() &&
        (current_time - mon->last_pll_lock_time) > PLL_LOCK_TIMEOUT_MS) {
        Fault_Report(FAULT_PLL_UNLOCK, FAULT_LEVEL_STOP);
    }
}
```

### 3.3 限幅保护

```c
/* 所有控制输出必须限幅 */
#define DUTY_MAX    0.95f
#define DUTY_MIN    0.05f
#define CURRENT_MAX 50.0f   /* A */
#define VDC_MAX     800.0f  /* V */

float32 Saturate(float32 value, float32 min, float32 max) {
    if (value > max) return max;
    if (value < min) return min;
    return value;
}

/* 多级限幅示例 */
float32 Current_Controller_Update(Current_Controller_t *ctrl,
                                  float32 i_ref, float32 i_fb) {
    /* 1. 参考限幅 */
    i_ref = Saturate(i_ref, -CURRENT_MAX, CURRENT_MAX);

    /* 2. PI计算 */
    float32 error = i_ref - i_fb;
    float32 output = ctrl->Kp * error + ctrl->integrator;

    /* 3. 输出限幅 */
    output = Saturate(output, ctrl->u_min, ctrl->u_max);

    /* 4. 条件积分 */
    if (output != ctrl->u_max && output != ctrl->u_min) {
        ctrl->integrator += ctrl->Ki * ctrl->Ts * error;
    }

    return output;
}
```

## 4. 中断安全规则

### 4.1 临界区保护

```c
/* 全局中断控制 */
#define ENTER_CRITICAL()    __disable_irq()
#define EXIT_CRITICAL()     __enable_irq()

/* 共享变量访问 */
typedef struct {
    volatile float32 alpha;
    volatile float32 beta;
    volatile bool updated;
} Shared_Voltage_t;

void ISR_PWM(void) {
    /* ISR中更新共享变量 */
    ENTER_CRITICAL();
    g_shared_voltage.alpha = adc_result[0];
    g_shared_voltage.beta = adc_result[1];
    g_shared_voltage.updated = true;
    EXIT_CRITICAL();
}

void Main_Loop(void) {
    if (g_shared_voltage.updated) {
        float32 va, vb;

        ENTER_CRITICAL();
        va = g_shared_voltage.alpha;
        vb = g_shared_voltage.beta;
        g_shared_voltage.updated = false;
        EXIT_CRITICAL();

        /* 使用va, vb进行计算 */
    }
}
```

### 4.2 ISR执行时间

```c
/* 测量ISR执行时间 */
void ISR_PWM(void) {
    uint32 start_cycles = DWT_CYCCNT;  /* Cortex-M DWT计数器 */

    /* ISR代码 */
    ADC_Trigger();
    Control_Loop();
    PWM_Update();

    uint32 end_cycles = DWT_CYCCNT;
    uint32 duration = end_cycles - start_cycles;

    /* 记录最大执行时间 */
    if (duration > g_isr_max_cycles) {
        g_isr_max_cycles = duration;
    }

    /* 超时报警 */
    if (duration > MAX_ISR_CYCLES) {
        g_fault_flags |= FAULT_ISR_OVERTIME;
    }
}
```

## 5. 禁止事项清单

### 绝对禁止

```c
/* ❌ 禁止递归 */
void recursive_function(int n) {
    if (n > 0) recursive_function(n-1);  /* 禁止！ */
}

/* ❌ 禁止动态内存 */
void bad_function(void) {
    float32 *p = malloc(sizeof(float32));  /* 禁止！ */
    free(p);
}

/* ❌ 禁止浮点比较相等 */
if (voltage == 0.0f) {  /* 禁止！ */

/* ✅ 正确做法 */
if (fabsf(voltage) < 1e-6f) {

/* ❌ 禁止未初始化变量 */
float32 current;  /* 未初始化 */
float32 result = current * 2.0f;

/* ✅ 正确做法 */
float32 current = 0.0f;

/* ❌ 禁止隐式类型转换 */
float32 f = 1.5;
int32 i = f;  /* 警告：隐式截断 */

/* ✅ 正确做法 */
float32 f = 1.5f;
int32 i = (int32)f;  /* 显式转换 */
```

### 控制算法专用禁止

```c
/* ❌ 禁止在中断中使用三角函数（耗时）*/
void ISR_PWM(void) {
    float32 sin_val = sinf(angle);  /* 禁止！使用查表法 */
}

/* ❌ 禁止除法（使用倒数乘法）*/
float32 duty = v_ref / v_dc;  /* 避免 */

/* ✅ 预计算倒数 */
float32 inv_vdc = 1.0f / v_dc;  /* 慢速环路计算 */
float32 duty = v_ref * inv_vdc;  /* 快速环路使用 */

/* ❌ 禁止链式赋值 */
a = b = c = 0.0f;  /* 禁止 */

/* ✅ 分别赋值 */
a = 0.0f;
b = 0.0f;
c = 0.0f;
```

## 6. 文档与注释规范

### 6.1 函数头注释

```c
/**
 * @brief PR控制器更新
 *
 * 实现准比例谐振控制器，用于交流电流无静差跟踪。
 * 离散化采用双线性变换，截止频率wc决定谐振峰宽度。
 *
 * @param[in]  ctrl      控制器句柄
 * @param[in]  ref       参考电流值 [A]
 * @param[in]  feedback  反馈电流值 [A]
 * @return     控制输出（调制比，范围[-1, 1]）
 *
 * @pre        ctrl已通过PR_Init初始化
 * @post       内部状态x[0],x[1]更新
 *
 * @timing     必须在每个采样周期调用，周期=ctrl->Ts
 * @warning    调用频率必须与初始化时Ts对应，否则不稳定
 *
 * @example
 *   PR_Controller_t pr;
 *   PR_Init(&pr, 0.5f, 50.0f, 10.0f, 314.16f, 0.0001f, 1.0f, -1.0f);
 *   while(1) {
 *       float32 u = PR_Update(&pr, i_ref, i_meas);
 *   }
 */
float32 PR_Update(PR_Controller_t *ctrl, float32 ref, float32 feedback);
```

### 6.2 版本控制注释

```c
/* 文件头 */
/******************************************************************************
 * @file    pr_controller.c
 * @brief   比例谐振控制器实现
 * @version 1.2.0
 * @date    2024-01-15
 * @author  Power Electronics Team
 *
 * @changelog
 * v1.2.0 (2024-01-15) - 添加频率自适应功能
 * v1.1.0 (2023-11-20) - 修复过调制时积分饱和问题
 * v1.0.0 (2023-09-01) - 初始版本
 ******************************************************************************/
```

## 7. 测试与验证

### 7.1 单元测试模板

```c
/* 测试框架：使用Unity或自定义 */
void test_pr_controller_step_response(void) {
    PR_Controller_t pr;
    PR_Init(&pr, 0.5f, 50.0f, 10.0f, 314.16f, 0.0001f, 1.0f, -1.0f);

    float32 ref = 10.0f;  /* 10A阶跃 */
    float32 feedback = 0.0f;
    float32 max_overshoot = 0.0f;

    for (int i = 0; i < 10000; i++) {
        float32 output = PR_Update(&pr, ref, feedback);

        /* 模拟被控对象（简化的RL负载）*/
        feedback += (output * 400.0f - feedback * 1.0f) * 0.0001f / 0.001f;

        /* 记录超调 */
        if (feedback > ref) {
            float32 os = (feedback - ref) / ref * 100.0f;
            if (os > max_overshoot) max_overshoot = os;
        }
    }

    /* 验证稳态误差 */
    TEST_ASSERT_FLOAT_WITHIN(0.1f, ref, feedback);

    /* 验证超调 */
    TEST_ASSERT_LESS_THAN(20.0f, max_overshoot);
}
```

### 7.2 硬件在环测试

```c
/* HIL测试配置 */
#define HIL_ENABLE      1

#if HIL_ENABLE
    #include "hil_interface.h"
    #define ADC_READ()  HIL_GetVoltage()
    #define PWM_WRITE(d) HIL_SetDuty(d)
#else
    #define ADC_READ()  HW_ADC_Read()
    #define PWM_WRITE(d) HW_PWM_Set(d)
#endif
```
