/**
 * @file ecu_actuators.c
 * @brief Automotive Actuator Control Logic (Injection, Spark, Fan, MIL)
 */

#include "ecu_actuators.h"
#include "ecu_diagnostics.h"
#include "ecu_sensors.h"
#include <string.h>

static fan_speed_t s_fan_state = FAN_OFF;

void actuators_init(void) {
    s_fan_state = FAN_OFF;
}

void actuators_calculate(ecu_state_t current_state, 
                         const sensor_inputs_t *sensors, 
                         actuator_outputs_t *actuators) {
    if (!sensors || !actuators) return;

    memset(actuators, 0, sizeof(actuator_outputs_t));

    /* Always update MIL Lamp status directly from diagnostic manager */
    actuators->mil_lamp = diag_calculate_mil_status();

    switch (current_state) {
        case ECU_STATE_OFF:
        case ECU_STATE_INIT:
        case ECU_STATE_SHUTDOWN:
            s_fan_state = FAN_OFF;
            actuators->fuel_injection_pw_ms = 0.0f;
            actuators->ignition_timing_deg = 0.0f;
            actuators->cooling_fan_state = FAN_OFF;
            actuators->throttle_actuator_pct = 0.0f;
            actuators->fuel_pump_relay = false;
            actuators->starter_relay_enable = false;
            break;

        case ECU_STATE_STANDBY:
            s_fan_state = (sensors->coolant_temp_c >= 100.0f) ? FAN_LOW_SPEED : FAN_OFF;
            actuators->fuel_injection_pw_ms = 0.0f;
            actuators->ignition_timing_deg = 0.0f;
            actuators->cooling_fan_state = s_fan_state;
            actuators->throttle_actuator_pct = 0.0f;
            actuators->fuel_pump_relay = true;
            actuators->starter_relay_enable = (sensors->engine_rpm < 400 && sensors->battery_voltage_v >= 9.0f);
            break;

        case ECU_STATE_RUNNING: {
            actuators->fuel_pump_relay = true;
            actuators->starter_relay_enable = false; /* Disengage starter once running */

            /* 1. Throttle plate tracking */
            actuators->throttle_actuator_pct = sensors->throttle_pos1_pct;

            /* 2. Base Fuel Injection Pulse Width */
            float map_factor = (sensors->manifold_pressure_kpa / 100.0f);
            if (map_factor < 0.2f) map_factor = 0.2f;
            float rpm_factor = 1.0f + ((float)sensors->engine_rpm / 3500.0f);
            float base_pw = 2.5f * map_factor * rpm_factor;

            /* Warmup enrichment below 60°C */
            if (sensors->coolant_temp_c < 60.0f) {
                float cold_enrich = 1.0f + (60.0f - sensors->coolant_temp_c) * 0.008f;
                base_pw *= cold_enrich;
            }
            if (base_pw > 20.0f) base_pw = 20.0f;
            actuators->fuel_injection_pw_ms = base_pw;

            /* 3. Ignition Timing Advance */
            float base_timing = 10.0f + ((float)sensors->engine_rpm / 250.0f);
            if (base_timing > 36.0f) base_timing = 36.0f;
            actuators->ignition_timing_deg = base_timing;

            /* 4. Cooling Fan Control with Hysteresis */
            if (sensors->coolant_temp_c >= ECT_OVERHEAT_WARNING_C) {
                s_fan_state = FAN_HIGH_SPEED;
            } else if (sensors->coolant_temp_c >= 95.0f) {
                s_fan_state = FAN_LOW_SPEED;
            } else if (sensors->coolant_temp_c <= 88.0f) {
                s_fan_state = FAN_OFF;
            }
            /* If between 88.0f and 95.0f, s_fan_state retains its previous value (hysteresis) */
            actuators->cooling_fan_state = s_fan_state;
            break;
        }

        case ECU_STATE_DEGRADED: {
            /* Limp-home safety derating */
            actuators->fuel_pump_relay = true;
            actuators->starter_relay_enable = false;

            /* Cap throttle plate command to max 25% */
            float limited_tps = sensors->throttle_pos1_pct;
            if (limited_tps > 25.0f) limited_tps = 25.0f;
            actuators->throttle_actuator_pct = limited_tps;

            /* Safe conservative fuel & spark */
            actuators->fuel_injection_pw_ms = 3.0f + (limited_tps * 0.04f);
            actuators->ignition_timing_deg = 8.0f; /* Fixed retarded spark */

            /* Conservative cooling: keep fan at least at LOW_SPEED */
            if (sensors->coolant_temp_c >= 95.0f) {
                s_fan_state = FAN_HIGH_SPEED;
            } else {
                s_fan_state = FAN_LOW_SPEED;
            }
            actuators->cooling_fan_state = s_fan_state;
            break;
        }

        case ECU_STATE_ERROR:
            /* Emergency Stop: fuel cut-off, ignition kill, max cooling */
            s_fan_state = FAN_HIGH_SPEED;
            actuators->fuel_injection_pw_ms = 0.0f;
            actuators->ignition_timing_deg = 0.0f;
            actuators->cooling_fan_state = FAN_HIGH_SPEED;
            actuators->throttle_actuator_pct = 0.0f;
            actuators->fuel_pump_relay = false;
            actuators->starter_relay_enable = false;
            break;

        default:
            break;
    }
}
