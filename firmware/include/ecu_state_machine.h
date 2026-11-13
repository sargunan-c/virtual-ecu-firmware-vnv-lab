/**
 * @file ecu_state_machine.h
 * @brief Automotive ECU Operating State Machine (FSM)
 */

#ifndef ECU_STATE_MACHINE_H
#define ECU_STATE_MACHINE_H

#include "ecu_types.h"

#ifdef __cplusplus
extern "C" {
#endif

void sm_init(void);
void sm_step(const sensor_inputs_t *sensors);
ecu_state_t sm_get_current_state(void);
ecu_state_t sm_get_previous_state(void);
const char* sm_state_to_string(ecu_state_t state);
void sm_request_transition(ecu_state_t requested_state);

#ifdef __cplusplus
}
#endif

#endif /* ECU_STATE_MACHINE_H */

