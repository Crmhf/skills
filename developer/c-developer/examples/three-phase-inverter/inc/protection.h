/*
 * protection.h - 故障保护管理
 */

#ifndef PROTECTION_H
#define PROTECTION_H

#include "types.h"

typedef enum {
    FAULT_NONE = 0,
    FAULT_OVER_CURRENT = (1 << 0),
    FAULT_OVER_VOLTAGE = (1 << 1),
    FAULT_UNDER_VOLTAGE = (1 << 2),
    FAULT_OVER_TEMP = (1 << 3),
    FAULT_IGBT_FAULT = (1 << 4),
    FAULT_GRID_LOST = (1 << 5),
    FAULT_PLL_UNLOCK = (1 << 6),
    FAULT_EMERGENCY_STOP = (1 << 7)
} FaultCode_t;

typedef struct {
    float32_t i_max;
    float32_t v_dc_max;
    float32_t v_dc_min;
    float32_t temp_max;
    uint16_t debounce_cycles;
} Protection_Thresholds_t;

typedef struct {
    Protection_Thresholds_t thresholds;
    FaultCode_t active_faults;
    FaultCode_t latched_faults;
    uint16_t debounce_counter[16];
    bool triggered;
} Protection_Manager_t;

void Protection_Init(Protection_Manager_t *mgr, const Protection_Thresholds_t *thresholds);
FaultCode_t Protection_Update(Protection_Manager_t *mgr,
                              float32_t i_a, float32_t i_b, float32_t i_c,
                              float32_t v_dc, float32_t temp);
void Protection_Clear(Protection_Manager_t *mgr);
bool Protection_IsSafe(const Protection_Manager_t *mgr);

#endif /* PROTECTION_H */
