/*
 * transforms.h - 坐标变换
 *
 * Clarke变换: abc -> αβ (静止坐标系)
 * Park变换:  αβ -> dq  (旋转坐标系)
 */

#ifndef TRANSFORMS_H
#define TRANSFORMS_H

#include "types.h"

/*=============================================================================
 * 数据类型
 *=============================================================================*/

typedef struct {
    float32_t a;
    float32_t b;
    float32_t c;
} ABC_t;

typedef struct {
    float32_t alpha;
    float32_t beta;
} AlphaBeta_t;

typedef struct {
    float32_t d;
    float32_t q;
} DQ_t;

/*=============================================================================
 * Clarke变换 (abc -> αβ)
 *=============================================================================*/

/**
 * @brief Clarke变换（等幅值变换）
 *
 * 变换矩阵（等幅值）：
 * [Vα]   2  [ 1    -1/2    -1/2  ] [Va]
 * [Vβ] = - * [ 0    √3/2    -√3/2 ] [Vb]
 *        3                         [Vc]
 */
static inline void Clarke_Transform(const ABC_t *abc, AlphaBeta_t *ab)
{
    ab->alpha = 0.66666667f * (abc->a - 0.5f * abc->b - 0.5f * abc->c);
    ab->beta  = 0.66666667f * (0.0f + SQRT3 * 0.5f * abc->b - SQRT3 * 0.5f * abc->c);
}

/**
 * @brief 反Clarke变换 (αβ -> abc)
 */
static inline void Inverse_Clarke(const AlphaBeta_t *ab, ABC_t *abc)
{
    abc->a = ab->alpha;
    abc->b = -0.5f * ab->alpha + SQRT3 * 0.5f * ab->beta;
    abc->c = -0.5f * ab->alpha - SQRT3 * 0.5f * ab->beta;
}

/*=============================================================================
 * Park变换 (αβ -> dq)
 *=============================================================================*/

/**
 * @brief Park变换（旋转坐标系）
 *
 * [Vd]   [ cosθ    sinθ  ] [Vα]
 * [Vq] = [ -sinθ   cosθ  ] [Vβ]
 */
static inline void Park_Transform(const AlphaBeta_t *ab, float32_t theta, DQ_t *dq)
{
    float32_t cos_theta = cosf(theta);
    float32_t sin_theta = sinf(theta);

    dq->d =  ab->alpha * cos_theta + ab->beta * sin_theta;
    dq->q = -ab->alpha * sin_theta + ab->beta * cos_theta;
}

/**
 * @brief 反Park变换 (dq -> αβ)
 */
static inline void Inverse_Park(const DQ_t *dq, float32_t theta, AlphaBeta_t *ab)
{
    float32_t cos_theta = cosf(theta);
    float32_t sin_theta = sinf(theta);

    ab->alpha = dq->d * cos_theta - dq->q * sin_theta;
    ab->beta  = dq->d * sin_theta + dq->q * cos_theta;
}

#endif /* TRANSFORMS_H */
