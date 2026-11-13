/**
 * @file ecu_state_machine.c
 * @brief Automotive ECU Operating Finite State Machine (FSM) Implementation
 */

#include "ecu_state_machine.h"
#include "ecu_diagnostics.h"
#include "ecu_sensors.h"

static ecu_state_t s_current_state = ECU_STATE_OFF;
static ecu_state_t s_previous_state = ECU_STATE_OFF;
static uint32_t s_state_ticks = 0;
static bool s_post_passed = false;

void sm_init(void) {
    s_current_state = ECU_STATE_OFF;
    s_previous_state = ECU_STATE_OFF;
    s_state_ticks = 0;
    s_post_passed = false;
}

static void transition_to(ecu_state_t new_state) {
    if (s_current_state != new_state) {
        s_previous_state = s_current_state;
        s_current_state = new_state;
        s_state_ticks = 0;
    }
}

void sm_step(const sensor_inputs_t *sensors) {
    if (!sensors) return;

    s_state_ticks++;

    /* Check for immediate shutdown on ignition drop (unless already OFF) */
    if (!sensors->ignition_switch && s_current_state != ECU_STATE_OFF && s_current_state != ECU_STATE_SHUTDOWN) {
        transition_to(ECU_STATE_SHUTDOWN);
        return;
    }

    switch (s_current_state) {
        case ECU_STATE_OFF:
            if (sensors->ignition_switch) {
                transition_to(ECU_STATE_INIT);
            }
            break;

        case ECU_STATE_INIT:
            /* Simulate Power-On Self Test (POST) */
            if (s_state_ticks >= 3) { /* 30 ms self-check */
                s_post_passed = true;
                transition_to(ECU_STATE_STANDBY);
            }
            break;

        case ECU_STATE_STANDBY:
            if (diag_has_critical_dtc()) {
                transition_to(ECU_STATE_ERROR);
            } else if (sensors->engine_rpm >= RPM_CRANKING_THRESHOLD) {
                if (diag_has_degraded_dtc()) {
                    transition_to(ECU_STATE_DEGRADED);
                } else {
                    transition_to(ECU_STATE_RUNNING);
                }
            }
            break;

        case ECU_STATE_RUNNING:
            if (diag_has_critical_dtc()) {
                transition_to(ECU_STATE_ERROR);
            } else if (diag_has_degraded_dtc()) {
                transition_to(ECU_STATE_DEGRADED);
            } else if (sensors->engine_rpm < 150) {
                /* Engine stall */
                transition_to(ECU_STATE_STANDBY);
            }
            break;

        case ECU_STATE_DEGRADED:
            if (diag_has_critical_dtc()) {
                transition_to(ECU_STATE_ERROR);
            } else if (!diag_has_degraded_dtc()) {
                /* All faults recovered! Return to normal running */
                transition_to(ECU_STATE_RUNNING);
            } else if (sensors->engine_rpm < 150) {
                transition_to(ECU_STATE_STANDBY);
            }
            break;

        case ECU_STATE_ERROR:
            /* Latch state until ignition cycle or reset */
            if (!sensors->ignition_switch) {
                transition_to(ECU_STATE_SHUTDOWN);
            }
            break;

        case ECU_STATE_SHUTDOWN:
            if (s_state_ticks >= 2) {
                transition_to(ECU_STATE_OFF);
            }
            break;

        default:
            transition_to(ECU_STATE_OFF);
            break;
    }
}

ecu_state_t sm_get_current_state(void) {
    return s_current_state;
}

ecu_state_t sm_get_previous_state(void) {
    return s_previous_state;
}

const char* sm_state_to_string(ecu_state_t state) {
    switch (state) {
        case ECU_STATE_OFF:      return "OFF";
        case ECU_STATE_INIT:     return "INIT";
        case ECU_STATE_STANDBY:  return "STANDBY";
        case ECU_STATE_RUNNING:  return "RUNNING";
        case ECU_STATE_DEGRADED: return "DEGRADED (LIMP-HOME)";
        case ECU_STATE_ERROR:    return "ERROR (EMERGENCY STOP)";
        case ECU_STATE_SHUTDOWN: return "SHUTDOWN";
        default:                 return "UNKNOWN";
    }
}

void sm_request_transition(ecu_state_t requested_state) {
    transition_to(requested_state);
}
