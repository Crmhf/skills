/*
 * srf_pll.h - 同步参考坐标系锁相环
 */

#ifndef SRF_PLL_H
#define SRF_PLL_H

#include "types.h"

typedef struct {
    float32_t Kp;
    float32_t Ki;
    float32_t w_ff;
    float32_t w_max;
    float32_t w_min;

    float32_t theta;
    float32_t omega;
    float32_t integrator;

    float32_t vd;
    float32_t vq;
    float32_t v_mag;

    bool locked;
    uint16_t lock_counter;
} SRF_PLL_t;

void SRF_PLL_Init(SRF_PLL_t *pll, float32_t Kp, float32_t Ki,
                  float32_t w_ff, float32_t w_max, float32_t w_min);
void SRF_PLL_Update(SRF_PLL_t *pll, float32_t v_alpha, float32_t v_beta);
void SRF_PLL_Reset(SRF_PLL_t *pll);
bool SRF_PLL_IsLocked(const SRF_PLL_t *pll);

#endif /* SRF_PLL_H */
