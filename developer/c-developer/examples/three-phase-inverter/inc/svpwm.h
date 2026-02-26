/*
 * svpwm.h - 空间矢量脉宽调制
 */

#ifndef SVPWM_H
#define SVPWM_H

#include "types.h"

typedef struct {
    float32_t duty_a;
    float32_t duty_b;
    float32_t duty_c;
    uint8_t sector;
} SVPWM_Result_t;

void SVPWM_Calculate(float32_t v_alpha, float32_t v_beta,
                     float32_t vdc, SVPWM_Result_t *result);

#endif /* SVPWM_H */
