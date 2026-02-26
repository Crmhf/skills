/*
 * inverter.c - 三相并网逆变器主控
 */

#include "inverter.h"
#include "svpwm.h"
#include <math.h>

/* 控制器参数 */
#define PR_KP           0.3f
#define PR_KR           30.0f
#define PR_WC           10.0f

#define PI_VDC_KP       0.5f
#define PI_VDC_KI       50.0f

#define PLL_KP          0.5f
#define PLL_KI          50.0f

#define U_MAX           0.95f   /* 最大调制比 */
#define U_MIN          -0.95f

void Inverter_Init(Inverter_Control_t *inv)
{
    /* 初始化采样值 */
    inv->i_a = inv->i_b = inv->i_c = 0.0f;
    inv->v_a = inv->v_b = inv->v_c = 0.0f;
    inv->v_dc = VDC_RATED;
    inv->temp_igbt = 25.0f;

    /* 初始化控制器 */
    PR_Init(&inv->pr_d, PR_KP, PR_KR, PR_WC, GRID_OMEGA,
            SAMPLING_PERIOD, U_MAX, U_MIN);
    PR_Init(&inv->pr_q, PR_KP, PR_KR, PR_WC, GRID_OMEGA,
            SAMPLING_PERIOD, U_MAX, U_MIN);

    PI_Init(&inv->pi_vdc, PI_VDC_KP, PI_VDC_KI,
            SAMPLING_PERIOD, I_RATED, -I_RATED);

    SRF_PLL_Init(&inv->pll, PLL_KP, PLL_KI, GRID_OMEGA,
                 GRID_OMEGA * 1.1f, GRID_OMEGA * 0.9f);

    /* 初始化保护 */
    Protection_Thresholds_t thresholds = {
        .i_max = I_RATED * 1.2f,
        .v_dc_max = VDC_RATED * 1.15f,
        .v_dc_min = VDC_RATED * 0.8f,
        .temp_max = 85.0f,
        .debounce_cycles = 10
    };
    Protection_Init(&inv->protection, &thresholds);

    /* 初始状态 */
    inv->mode = MODE_STANDBY;
    inv->i_d_ref = 0.0f;
    inv->i_q_ref = 0.0f;
    inv->v_dc_ref = VDC_RATED;
    inv->cycle_count = 0;
}

void Inverter_ControlLoop(Inverter_Control_t *inv)
{
    /* 1. 采样（实际系统由ADC中断触发） */
    /* ADC_Read_All(&inv->i_a, &inv->i_b, &inv->i_c, ...); */

    /* 2. 故障检测 */
    FaultCode_t fault = Protection_Update(&inv->protection,
                                          inv->i_a, inv->i_b, inv->i_c,
                                          inv->v_dc, inv->temp_igbt);
    if (fault != FAULT_NONE) {
        Inverter_FaultHandler(inv, fault);
        return;
    }

    /* 3. 坐标变换 */
    ABC_t i_abc = {inv->i_a, inv->i_b, inv->i_c};
    ABC_t v_abc = {inv->v_a, inv->v_b, inv->v_c};

    Clarke_Transform(&i_abc, &inv->i_ab);
    Clarke_Transform(&v_abc, &inv->v_ab);

    /* 4. 锁相环更新 */
    SRF_PLL_Update(&inv->pll, inv->v_ab.alpha, inv->v_ab.beta);

    /* 5. Park变换到旋转坐标系 */
    Park_Transform(&inv->i_ab, inv->pll.theta, &inv->i_dq);
    Park_Transform(&inv->v_ab, inv->pll.theta, &inv->v_dq);

    /* 6. 根据运行模式执行控制 */
    switch (inv->mode) {
        case MODE_RUNNING:
            /* 直流电压外环 -> d轴电流 */
            inv->i_d_ref = PI_Update(&inv->pi_vdc, inv->v_dc_ref, inv->v_dc);

            /* PR电流控制（在旋转坐标系等效为PI，或切换到静止坐标系PR） */
            /* 这里示例使用旋转坐标系的PI控制 */
            inv->v_d_cmd = PI_Update(&inv->pi_vdc, inv->i_d_ref, inv->i_dq.d) + inv->v_dq.d;
            inv->v_q_cmd = PI_Update(&inv->pi_vdc, inv->i_q_ref, inv->i_dq.q) + inv->v_dq.q;
            break;

        case MODE_STARTUP:
            /* 软启动 - 电流缓升 */
            inv->i_d_ref *= 0.99f;
            break;

        case MODE_STANDBY:
        default:
            inv->v_d_cmd = 0.0f;
            inv->v_q_cmd = 0.0f;
            break;
    }

    /* 7. 反Park变换到αβ坐标系 */
    AlphaBeta_t v_ab_cmd;
    DQ_t v_dq_cmd = {inv->v_d_cmd, inv->v_q_cmd};
    Inverse_Park(&v_dq_cmd, inv->pll.theta, &v_ab_cmd);

    /* 8. SVPWM调制 */
    SVPWM_Result_t svpwm;
    SVPWM_Calculate(v_ab_cmd.alpha, v_ab_cmd.beta, inv->v_dc, &svpwm);

    inv->duty_a = svpwm.duty_a;
    inv->duty_b = svpwm.duty_b;
    inv->duty_c = svpwm.duty_c;

    /* 9. 输出到PWM模块 */
    /* PWM_SetDuty(inv->duty_a, inv->duty_b, inv->duty_c); */

    /* 10. 计算功率 */
    inv->p_out = 1.5f * (inv->v_dq.d * inv->i_dq.d + inv->v_dq.q * inv->i_dq.q);
    inv->q_out = 1.5f * (inv->v_dq.q * inv->i_dq.d - inv->v_dq.d * inv->i_dq.q);
    inv->pf = inv->p_out / sqrtf(inv->p_out * inv->p_out + inv->q_out * inv->q_out);

    inv->cycle_count++;
}

void Inverter_SetPowerCommand(Inverter_Control_t *inv, float32_t p_ref, float32_t q_ref)
{
    /* 功率到电流转换 P = 3/2 * Vd * Id (假设Vq≈0) */
    float32_t v_d = inv->pll.vd;

    if (fabsf(v_d) > 10.0f) {
        inv->i_d_ref = p_ref / (1.5f * v_d);
        inv->i_q_ref = -q_ref / (1.5f * v_d);  /* 负号根据dq方向定义 */
    }

    /* 限幅 */
    float32_t i_mag = sqrtf(inv->i_d_ref * inv->i_d_ref + inv->i_q_ref * inv->i_q_ref);
    if (i_mag > I_RATED) {
        float32_t scale = I_RATED / i_mag;
        inv->i_d_ref *= scale;
        inv->i_q_ref *= scale;
    }
}

void Inverter_FaultHandler(Inverter_Control_t *inv, FaultCode_t fault)
{
    /* 立即关断PWM */
    /* PWM_Disable(); */

    inv->duty_a = 0.5f;
    inv->duty_b = 0.5f;
    inv->duty_c = 0.5f;

    /* 切换到故障模式 */
    inv->mode = MODE_FAULT;

    /* 重置控制器 */
    PR_Reset(&inv->pr_d);
    PR_Reset(&inv->pr_q);
    PI_Reset(&inv->pi_vdc);

    /* 故障记录 */
    /* Fault_Log(fault, inv->cycle_count); */
}

bool Inverter_IsRunning(const Inverter_Control_t *inv)
{
    return (inv->mode == MODE_RUNNING || inv->mode == MODE_STARTUP);
}
