/**
 * @file ecu_fault_injection.c
 * @brief Automotive Fault Injection Engine
 */

#include "ecu_fault_injection.h"
#include <string.h>

#define MAX_FAULT_CHANNELS 8

static fault_injection_config_t s_faults[MAX_FAULT_CHANNELS];

void fault_inject_init(void) {
    memset(s_faults, 0, sizeof(s_faults));
}

void fault_inject_set(fault_target_t target, fault_inject_type_t type, float fixed_value, uint32_t duration_ticks) {
    if (target >= MAX_FAULT_CHANNELS) return;

    s_faults[target].target = target;
    s_faults[target].type = type;
    s_faults[target].fixed_value = fixed_value;
    s_faults[target].duration_ticks = duration_ticks;
    s_faults[target].elapsed_ticks = 0;
    s_faults[target].is_active = (type != FAULT_INJECT_NONE);
}

void fault_inject_clear(fault_target_t target) {
    if (target < MAX_FAULT_CHANNELS) {
        memset(&s_faults[target], 0, sizeof(fault_injection_config_t));
    }
}

void fault_inject_clear_all(void) {
    memset(s_faults, 0, sizeof(s_faults));
}

bool fault_inject_is_active(fault_target_t target) {
    if (target < MAX_FAULT_CHANNELS) {
        return s_faults[target].is_active;
    }
    return false;
}

uint8_t fault_inject_get_active_mask(void) {
    uint8_t mask = 0;
    for (uint8_t i = 0; i < MAX_FAULT_CHANNELS; i++) {
        if (s_faults[i].is_active) {
            mask |= (1 << i);
        }
    }
    return mask;
}

void fault_inject_apply(sensor_inputs_t *inputs) {
    if (!inputs) return;

    for (uint8_t i = 0; i < MAX_FAULT_CHANNELS; i++) {
        if (!s_faults[i].is_active) continue;

        /* Check duration expiration if duration_ticks > 0 */
        if (s_faults[i].duration_ticks > 0) {
            s_faults[i].elapsed_ticks++;
            if (s_faults[i].elapsed_ticks >= s_faults[i].duration_ticks) {
                s_faults[i].is_active = false;
                continue;
            }
        }

        switch (s_faults[i].target) {
            case TARGET_SENSOR_ECT:
                if (s_faults[i].type == FAULT_INJECT_SHORT_TO_GND) {
                    inputs->coolant_temp_c = -45.0f;
                } else if (s_faults[i].type == FAULT_INJECT_SHORT_TO_VCC || s_faults[i].type == FAULT_INJECT_OPEN_CIRCUIT) {
                    inputs->coolant_temp_c = 148.0f;
                } else if (s_faults[i].type == FAULT_INJECT_STUCK_VALUE) {
                    inputs->coolant_temp_c = s_faults[i].fixed_value;
                }
                break;

            case TARGET_SENSOR_TPS:
                if (s_faults[i].type == FAULT_INJECT_SHORT_TO_GND) {
                    inputs->throttle_pos1_pct = -5.0f;
                } else if (s_faults[i].type == FAULT_INJECT_SHORT_TO_VCC) {
                    inputs->throttle_pos1_pct = 110.0f;
                } else if (s_faults[i].type == FAULT_INJECT_TPS_MISMATCH) {
                    /* Break dual channel correlation: alter TPS2 so TPS1 + TPS2 != 100% */
                    inputs->throttle_pos2_pct = s_faults[i].fixed_value;
                } else if (s_faults[i].type == FAULT_INJECT_STUCK_VALUE) {
                    inputs->throttle_pos1_pct = s_faults[i].fixed_value;
                }
                break;

            case TARGET_SENSOR_MAP:
                if (s_faults[i].type == FAULT_INJECT_SHORT_TO_GND) {
                    inputs->manifold_pressure_kpa = 5.0f;
                } else if (s_faults[i].type == FAULT_INJECT_SHORT_TO_VCC) {
                    inputs->manifold_pressure_kpa = 260.0f;
                } else if (s_faults[i].type == FAULT_INJECT_STUCK_VALUE) {
                    inputs->manifold_pressure_kpa = s_faults[i].fixed_value;
                }
                break;

            case TARGET_SENSOR_VBATT:
                if (s_faults[i].type == FAULT_INJECT_SHORT_TO_GND) {
                    inputs->battery_voltage_v = 0.0f;
                } else if (s_faults[i].type == FAULT_INJECT_STUCK_VALUE) {
                    inputs->battery_voltage_v = s_faults[i].fixed_value;
                }
                break;

            case TARGET_SENSOR_RPM:
                if (s_faults[i].type == FAULT_INJECT_SHORT_TO_GND) {
                    inputs->engine_rpm = 0;
                } else if (s_faults[i].type == FAULT_INJECT_STUCK_VALUE) {
                    inputs->engine_rpm = (uint16_t)s_faults[i].fixed_value;
                }
                break;

            case TARGET_COMM_CAN:
                if (s_faults[i].type == FAULT_INJECT_CAN_TIMEOUT) {
                    inputs->can_bus_connected = false;
                }
                break;

            default:
                break;
        }
    }
}
