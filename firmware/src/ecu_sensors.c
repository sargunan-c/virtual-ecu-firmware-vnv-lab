/**
 * @file ecu_sensors.c
 * @brief Automotive Sensor Acquisition, Range Checking & Dual-Channel Plausibility
 */

#include "ecu_sensors.h"
#include "ecu_diagnostics.h"
#include <math.h>

void sensors_init(void) {
    /* Ready for initialization */
}

void sensors_process(const sensor_inputs_t *raw_in, sensor_inputs_t *filtered_out) {
    if (!raw_in || !filtered_out) return;

    *filtered_out = *raw_in;

    /* 1. Coolant Temperature (ECT) Verification */
    bool ect_low = (raw_in->coolant_temp_c < ECT_MIN_VALID_C);
    bool ect_high = (raw_in->coolant_temp_c > ECT_MAX_VALID_C);
    bool ect_overheat = (raw_in->coolant_temp_c >= ECT_OVERHEAT_CRITICAL_C);

    diag_report_fault(DTC_P0117_ECT_CIRCUIT_LOW, ect_low);
    diag_report_fault(DTC_P0118_ECT_CIRCUIT_HIGH, ect_high);
    diag_report_fault(DTC_P0217_ENGINE_COOLANT_OVERTEMP, ect_overheat);

    if (ect_low || ect_high) {
        /* Fallback safe value for limp-home operation */
        filtered_out->coolant_temp_c = ECT_FALLBACK_DEFAULT_C;
    }

    /* 2. Throttle Position Sensor (TPS) Validation */
    bool tps1_low = (raw_in->throttle_pos1_pct < 0.0f);
    bool tps1_high = (raw_in->throttle_pos1_pct > 100.0f);
    diag_report_fault(DTC_P0122_TPS_CIRCUIT_LOW, tps1_low);
    diag_report_fault(DTC_P0123_TPS_CIRCUIT_HIGH, tps1_high);

    /* Clamp filtered TPS1 within physical limits */
    if (filtered_out->throttle_pos1_pct < 0.0f) filtered_out->throttle_pos1_pct = 0.0f;
    if (filtered_out->throttle_pos1_pct > 100.0f) filtered_out->throttle_pos1_pct = 100.0f;

    /* Dual-Channel Correlation Check (ASIL-B Safety Rule) */
    /* By design: TPS1 + TPS2 = 100.0% +/- tolerance */
    float correlation_sum = raw_in->throttle_pos1_pct + raw_in->throttle_pos2_pct;
    float correlation_error = fabsf(correlation_sum - 100.0f);
    bool tps_mismatch = (correlation_error > TPS_DUAL_MAX_TOLERANCE);
    diag_report_fault(DTC_P0121_TPS_RANGE_PERFORMANCE, tps_mismatch);

    /* 3. Manifold Absolute Pressure (MAP) */
    bool map_fault = (raw_in->manifold_pressure_kpa < MAP_MIN_VALID_KPA || 
                      raw_in->manifold_pressure_kpa > MAP_MAX_VALID_KPA);
    diag_report_fault(DTC_P0106_MAP_RANGE_PERFORMANCE, map_fault);
    if (map_fault) {
        filtered_out->manifold_pressure_kpa = MAP_FALLBACK_DEFAULT_KPA;
    }

    /* 4. Battery Voltage (VBATT) */
    bool vbatt_low = (raw_in->battery_voltage_v < VBATT_MIN_VALID_V);
    bool vbatt_high = (raw_in->battery_voltage_v > VBATT_MAX_VALID_V);
    diag_report_fault(DTC_P0562_SYSTEM_VOLTAGE_LOW, vbatt_low);
    diag_report_fault(DTC_P0563_SYSTEM_VOLTAGE_HIGH, vbatt_high);

    /* 5. Communication / CAN Gateway Heartbeat */
    bool can_lost = (!raw_in->can_bus_connected);
    diag_report_fault(DTC_U0100_LOST_COMM_ECM_GATEWAY, can_lost);
}

bool sensors_are_plausible(void) {
    return (!diag_has_critical_dtc());
}
