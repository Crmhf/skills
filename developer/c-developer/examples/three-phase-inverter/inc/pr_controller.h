/*
 * pr_controller.h - 比例谐振(PR)控制器
 *
 * 用于交流电流的无静差跟踪，适用于单相/三相逆变器的静止坐标系控制
 */

#ifndef PR_CONTROLLER_H
#define PR_CONTROLLER_H

#include "types.h"

/*=============================================================================
 * 数据结构
 *=============================================================================*/

typedef struct {
    /* 控制器参数 */
    float32_t Kp;           /* 比例增益 */
    float32_t Kr;           /* 谐振增益 */
    float32_t wc;           /* 截止频率 (rad/s) */
    float32_t w0;           /* 谐振角频率 (rad/s) */
    float32_t Ts;           /* 采样周期 (s) */
    float32_t u_max;        /* 输出上限 */
    float32_t u_min;        /* 输出下限 */

    /* 离散化系数（内部计算）*/
    float32_t b0, b1, b2;   /* 谐振部分分子系数 */
    float32_t a1, a2;       /* 谐振部分分母系数 (a0 = 1) */

    /* 状态变量 */
    float32_t x[2];         /* 延迟单元状态 [z^{-1}, z^{-2}] */
    float32_t y;            /* 当前输出 */

    /* 诊断 */
    bool saturated;         /* 饱和标志 */
} PR_Controller_t;

/*=============================================================================
 * 函数接口
 *=============================================================================*/

/**
 * @brief PR控制器初始化
 *
 * @param ctrl      控制器实例
 * @param Kp        比例增益
 * @param Kr        谐振增益
 * @param wc        截止频率 (rad/s)，典型值 5~15
 * @param w0        谐振角频率 (rad/s)，50Hz对应314.16
 * @param Ts        采样周期 (s)
 * @param u_max     输出上限
 * @param u_min     输出下限
 */
void PR_Init(PR_Controller_t *ctrl,
             float32_t Kp, float32_t Kr,
             float32_t wc, float32_t w0,
             float32_t Ts,
             float32_t u_max, float32_t u_min);

/**
 * @brief PR控制器更新（每采样周期调用）
 *
 * @param ctrl      控制器实例
 * @param ref       参考值
 * @param feedback  反馈值
 * @return          控制器输出
 */
float32_t PR_Update(PR_Controller_t *ctrl, float32_t ref, float32_t feedback);

/**
 * @brief 重置控制器状态
 */
void PR_Reset(PR_Controller_t *ctrl);

/**
 * @brief 更新谐振频率（用于频率自适应）
 */
void PR_SetFrequency(PR_Controller_t *ctrl, float32_t w0);

#endif /* PR_CONTROLLER_H */
