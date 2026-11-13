/**
 * @file main.c
 * @brief Standalone Virtual ECU CLI & Scenario Execution Engine
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ecu_firmware.h"

static void print_banner(void) {
    printf("==================================================================\n");
    printf("      VIRTUAL ECU FIRMWARE - AUTOMOTIVE V&V AUTOMATION LAB       \n");
    printf("  Target: Powertrain & Thermal Control Unit (PTCU) Simulator     \n");
    printf("  Standard: C11 / ISO 26262 ASIL-B / ISO 14229 UDS Diagnostics   \n");
    printf("==================================================================\n");
}

static void print_telemetry_json(const ecu_telemetry_t *t) {
    printf("{\n");
    printf("  \"cycle\": %u,\n", t->cycle_count);
    printf("  \"uptime_ms\": %u,\n", t->uptime_ms);
    printf("  \"state\": \"%s\",\n", sm_state_to_string(t->current_state));
    printf("  \"inputs\": {\n");
    printf("    \"coolant_temp_c\": %.2f,\n", t->filtered_inputs.coolant_temp_c);
    printf("    \"tps1_pct\": %.2f,\n", t->filtered_inputs.throttle_pos1_pct);
    printf("    \"tps2_pct\": %.2f,\n", t->filtered_inputs.throttle_pos2_pct);
    printf("    \"map_kpa\": %.2f,\n", t->filtered_inputs.manifold_pressure_kpa);
    printf("    \"vbatt_v\": %.2f,\n", t->filtered_inputs.battery_voltage_v);
    printf("    \"rpm\": %u\n", t->filtered_inputs.engine_rpm);
    printf("  },\n");
    printf("  \"actuators\": {\n");
    printf("    \"fuel_pw_ms\": %.2f,\n", t->actuators.fuel_injection_pw_ms);
    printf("    \"spark_advance_deg\": %.2f,\n", t->actuators.ignition_timing_deg);
    printf("    \"fan_mode\": %d,\n", (int)t->actuators.cooling_fan_state);
    printf("    \"mil_lamp\": %d,\n", (int)t->actuators.mil_lamp);
    printf("    \"throttle_cmd_pct\": %.2f\n", t->actuators.throttle_actuator_pct);
    printf("  },\n");
    printf("  \"active_dtc_count\": %u,\n", t->active_dtc_count);
    printf("  \"active_dtcs\": [");
    for (uint8_t i = 0; i < t->active_dtc_count; i++) {
        printf("\"0x%04X\"%s", t->active_dtcs[i], (i + 1 < t->active_dtc_count) ? ", " : "");
    }
    printf("]\n");
    printf("}\n");
}

int main(int argc, char *argv[]) {
    print_banner();

    ecu_init();

    bool json_mode = false;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--json") == 0) {
            json_mode = true;
        }
    }

    printf("[VirtualECU] Initializing ECU state machine...\n");
    sensor_inputs_t inputs;
    memset(&inputs, 0, sizeof(inputs));
    inputs.ignition_switch = true;
    inputs.coolant_temp_c = 85.0f;
    inputs.throttle_pos1_pct = 20.0f;
    inputs.throttle_pos2_pct = 80.0f;
    inputs.manifold_pressure_kpa = 101.3f;
    inputs.battery_voltage_v = 13.8f;
    inputs.engine_rpm = 800;
    inputs.can_bus_connected = true;

    ecu_set_inputs(&inputs);

    /* Step through POST into STANDBY then RUNNING */
    ecu_step(5);

    ecu_telemetry_t telem;
    ecu_get_telemetry(&telem);

    printf("[VirtualECU] State after startup sequence: %s\n", sm_state_to_string(telem.current_state));

    if (json_mode) {
        print_telemetry_json(&telem);
    } else {
        printf("[VirtualECU] Active DTCs: %u | MIL: %d | Fan: %d | Fuel PW: %.2f ms | Spark: %.2f deg\n",
               telem.active_dtc_count, (int)telem.actuators.mil_lamp, (int)telem.actuators.cooling_fan_state,
               telem.actuators.fuel_injection_pw_ms, telem.actuators.ignition_timing_deg);
    }

    return 0;
}
