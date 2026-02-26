/*
 * svpwm.c - 空间矢量脉宽调制实现
 */

#include "svpwm.h"
#include <math.h>

static uint8_t SVPWM_GetSector(float32_t v_alpha, float32_t v_beta)
{
    float32_t u1 = v_beta;
    float32_t u2 = 0.866025f * v_alpha - 0.5f * v_beta;
    float32_t u3 = -0.866025f * v_alpha - 0.5f * v_beta;

    uint8_t sector = 0;
    if (u1 > 0.0f) sector |= 1;
    if (u2 > 0.0f) sector |= 2;
    if (u3 > 0.0f) sector |= 4;

    return sector;
}

void SVPWM_Calculate(float32_t v_alpha, float32_t v_beta,
                     float32_t vdc, SVPWM_Result_t *result)
{
    /* 归一化 */
    float32_t val_n = v_alpha / vdc;
    float32_t vbe_n = v_beta / vdc;

    /* 中间变量 */
    float32_t X = vbe_n;
    float32_t Y = 0.866025f * val_n + 0.5f * vbe_n;
    float32_t Z = -0.866025f * val_n + 0.5f * vbe_n;

    /* 扇区判断 */
    uint8_t sector = SVPWM_GetSector(val_n, vbe_n);
    result->sector = sector;

    /* 计算基本矢量作用时间 */
    float32_t t1, t2;
    switch (sector) {
        case 1: t1 = -Z; t2 = X; break;
        case 2: t1 = Z;  t2 = Y; break;
        case 3: t1 = X;  t2 = -Y; break;
        case 4: t1 = -X; t2 = Z; break;
        case 5: t1 = -Y; t2 = -Z; break;
        case 6: t1 = Y;  t2 = -X; break;
        default: t1 = t2 = 0.0f; break;
    }

    /* 过调制处理 */
    float32_t sum = t1 + t2;
    if (sum > 1.0f) {
        t1 = t1 / sum;
        t2 = t2 / sum;
    }

    float32_t t0 = 1.0f - t1 - t2;

    /* 七段式SVPWM - 计算占空比 */
    float32_t ta, tb, tc;

    switch (sector) {
        case 1: /* V0-V1-V2-V7-V2-V1-V0, 扇区I (0-60°) */
            ta = 0.5f * t0;
            tb = 0.5f * t0 + t1;
            tc = 0.5f * t0 + t1 + t2;
            break;
        case 2: /* V0-V3-V2-V7-V2-V3-V0, 扇区II (60-120°) */
            ta = 0.5f * t0 + t2;
            tb = 0.5f * t0;
            tc = 0.5f * t0 + t1 + t2;
            break;
        case 3: /* V0-V3-V4-V7-V4-V3-V0, 扇区III (120-180°) */
            ta = 0.5f * t0 + t1 + t2;
            tb = 0.5f * t0;
            tc = 0.5f * t0 + t1;
            break;
        case 4: /* V0-V5-V4-V7-V4-V5-V0, 扇区IV (180-240°) */
            ta = 0.5f * t0 + t1 + t2;
            tb = 0.5f * t0 + t2;
            tc = 0.5f * t0;
            break;
        case 5: /* V0-V5-V6-V7-V6-V5-V0, 扇区V (240-300°) */
            ta = 0.5f * t0 + t1;
            tb = 0.5f * t0 + t1 + t2;
            tc = 0.5f * t0;
            break;
        case 6: /* V0-V1-V6-V7-V6-V1-V0, 扇区VI (300-360°) */
            ta = 0.5f * t0;
            tb = 0.5f * t0 + t1 + t2;
            tc = 0.5f * t0 + t2;
            break;
        default:
            ta = tb = tc = 0.5f;
            break;
    }

    result->duty_a = SATURATE(ta, 0.0f, 1.0f);
    result->duty_b = SATURATE(tb, 0.0f, 1.0f);
    result->duty_c = SATURATE(tc, 0.0f, 1.0f);
}
