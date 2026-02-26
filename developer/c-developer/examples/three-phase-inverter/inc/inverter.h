/*
 * inverter.h - 三相并网逆变器主控
 */

#ifndef INVERTER_H
#define INVERTER_H

#include "types.h"
#include "pr_controller.h"
#include "pi_controller.h"
#include "srf_pll.h"
#include "transforms.h"
#include "protection.h"

/*=============================================================================
 * 运行模式
 *=============================================================================*/
typedef enum {
    MODE_STANDBY = 0,       /* 待机 */
    MODE_PRECHARGE,         /* 预充电 */
    MODE_GRID_CHECK,        /* 电网检测 */
    MODE_STARTUP,           /* 软启动 */
    MODE_RUNNING,           /* 正常运行 */
    MODE_FAULT              /* 故障 */
} Inverter_Mode_t;

/*=============================================================================
 * 控制结构体
 *=============================================================================*/
typedef struct {
    /* 采样值 */
    float32_t i_a, i_b, i_c;        /* 三相电流 (A) */
    float32_t v_a, v_b, v_c;        /* 三相电压 (V) */
    float32_t v_dc;                 /* 直流母线电压 (V) */
    float32_t temp_igbt;            /* IGBT温度 (°C) */

    /* 坐标变换后 */
    AlphaBeta_t i_ab;               /* 电流αβ分量 */
    AlphaBeta_t v_ab;               /* 电压αβ分量 */
    DQ_t i_dq;                      /* 电流dq分量 */
    DQ_t v_dq;                      /* 电压dq分量 */

    /* 参考值 */
    float32_t i_d_ref;              /* d轴电流参考 (有功) */
    float32_t i_q_ref;              /* q轴电流参考 (无功) */
    float32_t v_dc_ref;             /* 直流电压参考 */

    /* 控制器 */
    PR_Controller_t pr_d;           /* d轴PR控制器 */
    PR_Controller_t pr_q;           /* q轴PR控制器 */
    PI_Controller_t pi_vdc;         /* 直流电压PI控制器 */
    SRF_PLL_t pll;                  /* 锁相环 */

    /* 输出 */
    float32_t duty_a, duty_b, duty_c;   /* PWM占空比 */
    float32_t v_d_cmd, v_q_cmd;         /* 电压指令 */

    /* 状态 */
    Inverter_Mode_t mode;
    Protection_Manager_t protection;
    uint32_t cycle_count;

    /* 诊断 */
    float32_t p_out;                /* 输出功率 */
    float32_t q_out;                /* 无功功率 */
    float32_t pf;                   /* 功率因数 */
} Inverter_Control_t;

/*=============================================================================
 * 函数接口
 *=============================================================================*/

void Inverter_Init(Inverter_Control_t *inv);
void Inverter_ControlLoop(Inverter_Control_t *inv);
void Inverter_SetPowerCommand(Inverter_Control_t *inv, float32_t p_ref, float32_t q_ref);
void Inverter_FaultHandler(Inverter_Control_t *inv, FaultCode_t fault);
bool Inverter_IsRunning(const Inverter_Control_t *inv);

#endif /* INVERTER_H */
