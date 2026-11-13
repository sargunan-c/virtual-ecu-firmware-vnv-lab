/**
 * @file ecu_actuators.h
 * @brief Automotive Actuator Control Logic (Injection, Ignition, Fan, Throttle)
 */

#ifndef ECU_ACTUATORS_H
#define ECU_ACTUATORS_H

#include "ecu_types.h"

#ifdef __cplusplus
extern "C" {
#endif

void actuators_init(void);
void actuators_calculate(ecu_state_t current_state, 
                         const sensor_inputs_t *sensors, 
                         actuator_outputs_t *actuators);

#ifdef __cplusplus
}
#endif

#endif /* ECU_ACTUATORS_H */
