/**
 * @file ecu_fault_injection.h
 * @brief Fault Injection Engine for Simulating Electrical & Protocol Failures
 */

#ifndef ECU_FAULT_INJECTION_H
#define ECU_FAULT_INJECTION_H

#include "ecu_types.h"

#ifdef __cplusplus
extern "C" {
#endif

void fault_inject_init(void);
void fault_inject_set(fault_target_t target, fault_inject_type_t type, float fixed_value, uint32_t duration_ticks);
void fault_inject_clear(fault_target_t target);
void fault_inject_clear_all(void);
void fault_inject_apply(sensor_inputs_t *inputs);
bool fault_inject_is_active(fault_target_t target);
uint8_t fault_inject_get_active_mask(void);

#ifdef __cplusplus
}
#endif

#endif /* ECU_FAULT_INJECTION_H */

