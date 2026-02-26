/*
 * pi_controller.h - PI控制器
 */

#ifndef PI_CONTROLLER_H
#define PI_CONTROLLER_H

#include "types.h"

typedef struct {
    float32_t Kp;
    float32_t Ki;
    float32_t Ts;
    float32_t u_max;
    float32_t u_min;

    float32_t integrator;
    float32_t prev_error;
    float32_t output;
    bool saturated;
} PI_Controller_t;

void PI_Init(PI_Controller_t *ctrl, float32_t Kp, float32_t Ki,
             float32_t Ts, float32_t u_max, float32_t u_min);
float32_t PI_Update(PI_Controller_t *ctrl, float32_t ref, float32_t feedback);
void PI_Reset(PI_Controller_t *ctrl);

#endif /* PI_CONTROLLER_H */
