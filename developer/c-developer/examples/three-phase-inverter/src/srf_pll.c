/*
 * srf_pll.c - 同步参考坐标系锁相环
 */

#include "srf_pll.h"
#include <math.h>

#define LOCK_THRESHOLD  0.05f
#define LOCK_COUNT      100

void SRF_PLL_Init(SRF_PLL_t *pll, float32_t Kp, float32_t Ki,
                  float32_t w_ff, float32_t w_max, float32_t w_min)
{
    pll->Kp = Kp;
    pll->Ki = Ki;
    pll->w_ff = w_ff;
    pll->w_max = w_max;
    pll->w_min = w_min;
    SRF_PLL_Reset(pll);
}

void SRF_PLL_Reset(SRF_PLL_t *pll)
{
    pll->theta = 0.0f;
    pll->omega = pll->w_ff;
    pll->integrator = 0.0f;
    pll->vd = 0.0f;
    pll->vq = 0.0f;
    pll->v_mag = 0.0f;
    pll->locked = false;
    pll->lock_counter = 0;
}

void SRF_PLL_Update(SRF_PLL_t *pll, float32_t v_alpha, float32_t v_beta)
{
    /* Park变换 */
    float32_t cos_theta = cosf(pll->theta);
    float32_t sin_theta = sinf(pll->theta);

    pll->vd =  v_alpha * cos_theta + v_beta * sin_theta;
    pll->vq = -v_alpha * sin_theta + v_beta * cos_theta;

    /* 电压幅值 */
    pll->v_mag = sqrtf(v_alpha * v_alpha + v_beta * v_beta);

    /* 相位误差 - Vq应为0 */
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

    /* 归一化到 [0, 2π) */
    while (pll->theta >= PI2) pll->theta -= PI2;
    while (pll->theta < 0.0f) pll->theta += PI2;

    /* 锁定检测 - Vq足够小且持续一段时间 */
    if (fabsf(pll->vq) / pll->v_mag < LOCK_THRESHOLD) {
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

bool SRF_PLL_IsLocked(const SRF_PLL_t *pll)
{
    return pll->locked;
}
