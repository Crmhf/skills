/*
 * types.h - 通用类型定义
 * 版本: 1.0.0
 */

#ifndef TYPES_H
#define TYPES_H

#include <stdint.h>
#include <stdbool.h>

/*=============================================================================
 * 基本类型定义
 *=============================================================================*/
typedef float       float32_t;
typedef double      float64_t;

typedef int8_t      int8_t;
typedef int16_t     int16_t;
typedef int32_t     int32_t;
typedef uint8_t     uint8_t;
typedef uint16_t    uint16_t;
typedef uint32_t    uint32_t;

/*=============================================================================
 * 数学常量
 *=============================================================================*/
#define PI          3.14159265358979323846f
#define PI2         (2.0f * PI)
#define PI_HALF     (PI / 2.0f)
#define SQRT3       1.7320508075688772f
#define INV_SQRT3   (0.5773502691896258f)   /* 1/sqrt(3) */
#define SQRT2       1.4142135623730951f
#define INV_SQRT2   (0.7071067811865475f)   /* 1/sqrt(2) */

/*=============================================================================
 * 系统参数
 *=============================================================================*/
#define SAMPLING_FREQUENCY_HZ   20000.0f    /* ADC采样频率 */
#define SAMPLING_PERIOD         (1.0f / SAMPLING_FREQUENCY_HZ)
#define PWM_FREQUENCY_HZ        10000.0f    /* PWM开关频率 */

#define GRID_FREQUENCY_HZ       50.0f       /* 电网频率 */
#define GRID_OMEGA              (2.0f * PI * GRID_FREQUENCY_HZ)

#define VDC_RATED               700.0f      /* 额定直流母线电压 (V) */
#define VGRID_LL_RATED          380.0f      /* 电网线电压 (V) */
#define VGRID_PH_RATED          (VGRID_LL_RATED * INV_SQRT3)  /* 相电压峰值 */

#define I_RATED                 100.0f      /* 额定电流 (A) */
#define POWER_RATED             50000.0f    /* 额定功率 (W) */

/*=============================================================================
 * 实用宏
 *=============================================================================*/
#define SATURATE(x, min, max)   (((x) > (max)) ? (max) : (((x) < (min)) ? (min) : (x)))
#define ABS(x)                  (((x) >= 0.0f) ? (x) : -(x))
#define SIGN(x)                 (((x) >= 0.0f) ? 1.0f : -1.0f)
#define MAX(a, b)               (((a) > (b)) ? (a) : (b))
#define MIN(a, b)               (((a) < (b)) ? (a) : (b))

/* 浮点比较 */
#define EPSILON_F32             1e-6f
#define FLOAT_EQ(a, b)          (ABS((a) - (b)) < EPSILON_F32)
#define FLOAT_IS_ZERO(x)        (ABS(x) < EPSILON_F32)

#endif /* TYPES_H */
