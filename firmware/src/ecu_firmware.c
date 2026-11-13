/**
 * @file ecu_firmware.c
 * @brief Top-Level Virtual ECU Firmware Integration & Harness Interface
 */

#ifndef BUILDING_ECU_DLL
#define BUILDING_ECU_DLL
#endif
#include "ecu_firmware.h"
#include <string.h>

static sensor_inputs_t   s_raw_inputs;
static sensor_inputs_t   s_injected_inputs;
static sensor_inputs_t   s_filtered_inputs;
static actuator_outputs_t s_actuators;
static ecu_telemetry_t   s_telemetry;
static uint32_t          s_cycle_count = 0;

static void set_default_nominal_inputs(sensor_inputs_t *inputs) {
    inputs->coolant_temp_c = 85.0f;
    inputs->throttle_pos1_pct = 20.0f;
    inputs->throttle_pos2_pct = 80.0f;  /* 100 - 20 = 80 */
    inputs->manifold_pressure_kpa = 101.3f;
    inputs->battery_voltage_v = 13.8f;
    inputs->engine_rpm = 800;
    inputs->ignition_switch = true;
    inputs->engine_crank_request = false;
    inputs->can_bus_connected = true;
}

void ecu_init(void) {
    s_cycle_count = 0;
    memset(&s_telemetry, 0, sizeof(s_telemetry));
    
    diag_init();
    sensors_init();
    actuators_init();
    sm_init();
    fault_inject_init();

    set_default_nominal_inputs(&s_raw_inputs);
    s_injected_inputs = s_raw_inputs;
    s_filtered_inputs = s_raw_inputs;
    memset(&s_actuators, 0, sizeof(s_actuators));
}

void ecu_reset(void) {
    ecu_init();
}

void ecu_set_inputs(const sensor_inputs_t *inputs) {
    if (inputs) {
        s_raw_inputs = *inputs;
    }
}

void ecu_get_inputs(sensor_inputs_t *inputs) {
    if (inputs) {
        *inputs = s_raw_inputs;
    }
}

void ecu_step(uint32_t step_count) {
    if (step_count == 0) step_count = 1;

    for (uint32_t i = 0; i < step_count; i++) {
        s_cycle_count++;

        /* 1. Apply Fault Injection to simulate physical signal manipulation */
        s_injected_inputs = s_raw_inputs;
        fault_inject_apply(&s_injected_inputs);

        /* 2. Sensor Processing & Boundary Verification */
        sensors_process(&s_injected_inputs, &s_filtered_inputs);

        /* 3. Diagnostic Manager Step */
        diag_step();

        /* 4. State Machine Execution */
        sm_step(&s_filtered_inputs);

        /* 5. Actuator Control Calculation */
        actuators_calculate(sm_get_current_state(), &s_filtered_inputs, &s_actuators);
    }

    /* Update Telemetry Record */
    s_telemetry.cycle_count = s_cycle_count;
    s_telemetry.uptime_ms = s_cycle_count * ECU_TICK_RATE_MS;
    s_telemetry.current_state = sm_get_current_state();
    s_telemetry.previous_state = sm_get_previous_state();
    s_telemetry.raw_inputs = s_raw_inputs;
    s_telemetry.filtered_inputs = s_filtered_inputs;
    s_telemetry.actuators = s_actuators;
    s_telemetry.active_dtc_count = diag_get_active_dtc_count();
    diag_get_active_dtcs(s_telemetry.active_dtcs, ECU_MAX_ACTIVE_DTCS);
    s_telemetry.limp_home_active = (sm_get_current_state() == ECU_STATE_DEGRADED);
    s_telemetry.emergency_stop_active = (sm_get_current_state() == ECU_STATE_ERROR);
    s_telemetry.post_passed = true;
}

void ecu_get_telemetry(ecu_telemetry_t *telemetry) {
    if (telemetry) {
        *telemetry = s_telemetry;
    }
}

ecu_state_t ecu_get_state(void) {
    return sm_get_current_state();
}

void ecu_inject_fault(uint8_t target, uint8_t type, float fixed_value, uint32_t duration_ticks) {
    fault_inject_set((fault_target_t)target, (fault_inject_type_t)type, fixed_value, duration_ticks);
}

void ecu_clear_fault(uint8_t target) {
    fault_inject_clear((fault_target_t)target);
}

void ecu_clear_all_faults(void) {
    fault_inject_clear_all();
}

void ecu_clear_diagnostics(void) {
    diag_clear_all_dtcs();
}

bool ecu_is_dtc_active(uint16_t dtc) {
    return diag_is_dtc_confirmed((dtc_code_t)dtc);
}

uint8_t ecu_get_active_dtc_count(void) {
    return diag_get_active_dtc_count();
}

void ecu_get_active_dtc_list(uint16_t *dtc_list, uint8_t max_count) {
    diag_get_active_dtcs(dtc_list, max_count);
}
