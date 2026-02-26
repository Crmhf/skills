/*
 * pr_controller.c - 比例谐振(PR)控制器实现
 */

#include "pr_controller.h"
#include <math.h>

void PR_Init(PR_Controller_t *ctrl, float32_t Kp, float32_t Kr,
             float32_t wc, float32_t w0, float32_t Ts,
             float32_t u_max, float32_t u_min)
{
    ctrl->Kp = Kp;
    ctrl->Kr = Kr;
    ctrl->wc = wc;
    ctrl->w0 = w0;
    ctrl->Ts = Ts;
    ctrl->u_max = u_max;
    ctrl->u_min = u_min;

    PR_Reset(ctrl);
    PR_SetFrequency(ctrl, w0);
}

void PR_SetFrequency(PR_Controller_t *ctrl, float32_t w0)
{
    ctrl->w0 = w0;

    /* 预畸变双线性变换处理频率 */
    float32_t wd = (2.0f / ctrl->Ts) * tanf(w0 * ctrl->Ts / 2.0f);
    float32_t c = 2.0f / ctrl->Ts;

    float32_t wd_sq = wd * wd;
    float32_t wc_c = ctrl->wc * c;
    float32_t c_sq = c * c;

    /* 准PR传递函数: G(s) = 2*wc*s / (s^2 + 2*wc*s + wd^2) */
    float32_t denom = c_sq + 2.0f * ctrl->wc * c + wd_sq;

    /* 双线性变换离散化 */
    ctrl->b0 = (2.0f * wc_c) / denom;
    ctrl->b1 = 0.0f;
    ctrl->b2 = (-2.0f * wc_c) / denom;

    ctrl->a1 = (2.0f * wd_sq - 2.0f * c_sq) / denom;
    ctrl->a2 = (c_sq - 2.0f * wc_c + wd_sq) / denom;
}

float32_t PR_Update(PR_Controller_t *ctrl, float32_t ref, float32_t feedback)
{
    float32_t error = ref - feedback;

    /* 比例部分 */
    float32_t up = ctrl->Kp * error;

    /* 谐振部分 - 直接II型实现 */
    float32_t w = error - ctrl->a1 * ctrl->x[0] - ctrl->a2 * ctrl->x[1];
    float32_t ur = ctrl->Kr * (ctrl->b0 * w + ctrl->b1 * ctrl->x[0] + ctrl->b2 * ctrl->x[1]);

    /* 更新状态 */
    ctrl->x[1] = ctrl->x[0];
    ctrl->x[0] = w;

    /* 总输出 */
    float32_t output = up + ur;

    /* 输出限幅 */
    ctrl->saturated = false;
    if (output > ctrl->u_max) {
        output = ctrl->u_max;
        ctrl->saturated = true;
    } else if (output < ctrl->u_min) {
        output = ctrl->u_min;
        ctrl->saturated = true;
    }

    ctrl->y = output;
    return output;
}

void PR_Reset(PR_Controller_t *ctrl)
{
    ctrl->x[0] = 0.0f;
    ctrl->x[1] = 0.0f;
    ctrl->y = 0.0f;
    ctrl->saturated = false;
}
