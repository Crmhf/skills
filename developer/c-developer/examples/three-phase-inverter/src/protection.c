/*
 * protection.c - 故障保护管理
 */

#include "protection.h"

void Protection_Init(Protection_Manager_t *mgr, const Protection_Thresholds_t *thresholds)
{
    mgr->thresholds = *thresholds;
    mgr->active_faults = FAULT_NONE;
    mgr->latched_faults = FAULT_NONE;
    mgr->triggered = false;

    for (int i = 0; i < 16; i++) {
        mgr->debounce_counter[i] = 0;
    }
}

FaultCode_t Protection_Update(Protection_Manager_t *mgr,
                              float32_t i_a, float32_t i_b, float32_t i_c,
                              float32_t v_dc, float32_t temp)
{
    FaultCode_t new_faults = FAULT_NONE;

    /* 过流检测 - 三相瞬时最大值 */
    float32_t i_max = 0.0f;
    float32_t i_abs_a = ABS(i_a);
    float32_t i_abs_b = ABS(i_b);
    float32_t i_abs_c = ABS(i_c);

    if (i_abs_a > i_max) i_max = i_abs_a;
    if (i_abs_b > i_max) i_max = i_abs_b;
    if (i_abs_c > i_max) i_max = i_abs_c;

    if (i_max > mgr->thresholds.i_max) {
        new_faults |= FAULT_OVER_CURRENT;
    }

    /* 直流过压检测 */
    if (v_dc > mgr->thresholds.v_dc_max) {
        new_faults |= FAULT_OVER_VOLTAGE;
    }

    /* 直流欠压检测 */
    if (v_dc < mgr->thresholds.v_dc_min) {
        new_faults |= FAULT_UNDER_VOLTAGE;
    }

    /* 过温检测 */
    if (temp > mgr->thresholds.temp_max) {
        new_faults |= FAULT_OVER_TEMP;
    }

    /* 去抖处理 */
    FaultCode_t confirmed = FAULT_NONE;
    for (int i = 0; i < 8; i++) {
        if (new_faults & (1u << i)) {
            if (mgr->debounce_counter[i] < mgr->thresholds.debounce_cycles) {
                mgr->debounce_counter[i]++;
            } else {
                confirmed |= (1u << i);
            }
        } else {
            mgr->debounce_counter[i] = 0;
        }
    }

    mgr->active_faults = confirmed;
    mgr->latched_faults |= confirmed;

    if (confirmed != FAULT_NONE) {
        mgr->triggered = true;
    }

    return confirmed;
}

void Protection_Clear(Protection_Manager_t *mgr)
{
    mgr->active_faults = FAULT_NONE;
    mgr->latched_faults = FAULT_NONE;
    mgr->triggered = false;

    for (int i = 0; i < 16; i++) {
        mgr->debounce_counter[i] = 0;
    }
}

bool Protection_IsSafe(const Protection_Manager_t *mgr)
{
    return (mgr->active_faults == FAULT_NONE);
}
