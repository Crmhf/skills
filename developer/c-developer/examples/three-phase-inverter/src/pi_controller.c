/*
 * pi_controller.c - PI控制器实现
 */

#include "pi_controller.h"

void PI_Init(PI_Controller_t *ctrl, float32_t Kp, float32_t Ki,
             float32_t Ts, float32_t u_max, float32_t u_min)
{
    ctrl->Kp = Kp;
    ctrl->Ki = Ki;
    ctrl->Ts = Ts;
    ctrl->u_max = u_max;
    ctrl->u_min = u_min;
    PI_Reset(ctrl);
}

float32_t PI_Update(PI_Controller_t *ctrl, float32_t ref, float32_t feedback)
{
    float32_t error = ref - feedback;

    /* 比例项 */
    float32_t P = ctrl->Kp * error;

    /* 积分项（带条件积分抗饱和） */
    float32_t I_new = ctrl->integrator + ctrl->Ki * ctrl->Ts * error;

    /* 计算临时输出 */
    float32_t output = P + I_new;

    /* 条件积分 - 只有未饱和时才更新积分器 */
    ctrl->saturated = false;
    if (output > ctrl->u_max) {
        output = ctrl->u_max;
        ctrl->saturated = true;
        /* 正误差时不积分 */
        if (error < 0.0f) {
            ctrl->integrator = I_new;
        }
    } else if (output < ctrl->u_min) {
        output = ctrl->u_min;
        ctrl->saturated = true;
        /* 负误差时不积分 */
        if (error > 0.0f) {
            ctrl->integrator = I_new;
        }
    } else {
        /* 未饱和，正常积分 */
        ctrl->integrator = I_new;
    }

    ctrl->prev_error = error;
    ctrl->output = output;
    return output;
}

void PI_Reset(PI_Controller_t *ctrl)
{
    ctrl->integrator = 0.0f;
    ctrl->prev_error = 0.0f;
    ctrl->output = 0.0f;
    ctrl->saturated = false;
}
