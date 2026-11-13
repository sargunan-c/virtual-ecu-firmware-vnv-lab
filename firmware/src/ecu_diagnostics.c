/**
 * @file ecu_diagnostics.c
 * @brief Diagnostic Trouble Code Management with ISO 14229 / AUTOSAR DEM style debounce
 */

#include "ecu_diagnostics.h"
#include <string.h>

#define MAX_TRACKED_DTCS 16

static dtc_record_t s_dtc_table[MAX_TRACKED_DTCS];
static uint8_t s_tracked_count = 0;
static uint32_t s_diag_ticks = 0;

static const uint16_t SUPPORTED_DTCS[] = {
    DTC_P0115_ECT_CIRCUIT_MALFUNCTION,
    DTC_P0117_ECT_CIRCUIT_LOW,
    DTC_P0118_ECT_CIRCUIT_HIGH,
    DTC_P0217_ENGINE_COOLANT_OVERTEMP,
    DTC_P0120_TPS_CIRCUIT_MALFUNCTION,
    DTC_P0121_TPS_RANGE_PERFORMANCE,
    DTC_P0122_TPS_CIRCUIT_LOW,
    DTC_P0123_TPS_CIRCUIT_HIGH,
    DTC_P0105_MAP_CIRCUIT_MALFUNCTION,
    DTC_P0106_MAP_RANGE_PERFORMANCE,
    DTC_P0560_SYSTEM_VOLTAGE_MALFUNCTION,
    DTC_P0562_SYSTEM_VOLTAGE_LOW,
    DTC_P0563_SYSTEM_VOLTAGE_HIGH,
    DTC_P0606_ECU_INTERNAL_FAULT,
    DTC_U0100_LOST_COMM_ECM_GATEWAY
};
#define SUPPORTED_DTCS_COUNT (sizeof(SUPPORTED_DTCS) / sizeof(SUPPORTED_DTCS[0]))

void diag_init(void) {
    memset(s_dtc_table, 0, sizeof(s_dtc_table));
    s_tracked_count = 0;
    s_diag_ticks = 0;

    for (size_t i = 0; i < SUPPORTED_DTCS_COUNT && i < MAX_TRACKED_DTCS; i++) {
        s_dtc_table[i].dtc_code = SUPPORTED_DTCS[i];
        s_dtc_table[i].status_mask = 0;
        s_dtc_table[i].consecutive_fail_count = 0;
        s_dtc_table[i].consecutive_pass_count = 0;
        s_dtc_table[i].first_fault_tick = 0;
        s_dtc_table[i].last_fault_tick = 0;
        s_tracked_count++;
    }
}

void diag_report_fault(dtc_code_t dtc, bool is_failing) {
    for (uint8_t i = 0; i < s_tracked_count; i++) {
        if (s_dtc_table[i].dtc_code == (uint16_t)dtc) {
            if (is_failing) {
                s_dtc_table[i].consecutive_pass_count = 0;
                if (s_dtc_table[i].consecutive_fail_count < 255) {
                    s_dtc_table[i].consecutive_fail_count++;
                }

                s_dtc_table[i].status_mask |= DTC_STATUS_TEST_FAILED;
                s_dtc_table[i].status_mask |= DTC_STATUS_TEST_FAILED_THIS_CYCLE;
                s_dtc_table[i].last_fault_tick = s_diag_ticks;

                if (s_dtc_table[i].consecutive_fail_count >= 1) {
                    s_dtc_table[i].status_mask |= DTC_STATUS_PENDING;
                }

                if (s_dtc_table[i].consecutive_fail_count >= DTC_DEBOUNCE_CONFIRM_CYCLES) {
                    if (!(s_dtc_table[i].status_mask & DTC_STATUS_CONFIRMED)) {
                        s_dtc_table[i].first_fault_tick = s_diag_ticks;
                    }
                    s_dtc_table[i].status_mask |= DTC_STATUS_CONFIRMED;
                    s_dtc_table[i].status_mask |= DTC_STATUS_WARNING_INDICATOR_REQUESTED;
                }
            } else {
                s_dtc_table[i].consecutive_fail_count = 0;
                if (s_dtc_table[i].consecutive_pass_count < 255) {
                    s_dtc_table[i].consecutive_pass_count++;
                }

                /* Clear immediate test failed bit */
                s_dtc_table[i].status_mask &= ~DTC_STATUS_TEST_FAILED;

                /* Heal confirmed DTC after consecutive clean cycles */
                if (s_dtc_table[i].consecutive_pass_count >= DTC_DEBOUNCE_HEAL_CYCLES) {
                    s_dtc_table[i].status_mask &= ~DTC_STATUS_CONFIRMED;
                    s_dtc_table[i].status_mask &= ~DTC_STATUS_PENDING;
                    s_dtc_table[i].status_mask &= ~DTC_STATUS_WARNING_INDICATOR_REQUESTED;
                }
            }
            break;
        }
    }
}

void diag_clear_all_dtcs(void) {
    for (uint8_t i = 0; i < s_tracked_count; i++) {
        s_dtc_table[i].status_mask = 0;
        s_dtc_table[i].consecutive_fail_count = 0;
        s_dtc_table[i].consecutive_pass_count = 0;
        s_dtc_table[i].first_fault_tick = 0;
        s_dtc_table[i].last_fault_tick = 0;
    }
}

uint8_t diag_get_active_dtc_count(void) {
    uint8_t count = 0;
    for (uint8_t i = 0; i < s_tracked_count; i++) {
        if (s_dtc_table[i].status_mask & DTC_STATUS_CONFIRMED) {
            count++;
        }
    }
    return count;
}

void diag_get_active_dtcs(uint16_t *out_dtcs, uint8_t max_count) {
    if (!out_dtcs || max_count == 0) return;
    uint8_t written = 0;
    for (uint8_t i = 0; i < s_tracked_count && written < max_count; i++) {
        if (s_dtc_table[i].status_mask & DTC_STATUS_CONFIRMED) {
            out_dtcs[written++] = s_dtc_table[i].dtc_code;
        }
    }
}

bool diag_is_dtc_confirmed(dtc_code_t dtc) {
    for (uint8_t i = 0; i < s_tracked_count; i++) {
        if (s_dtc_table[i].dtc_code == (uint16_t)dtc) {
            return (s_dtc_table[i].status_mask & DTC_STATUS_CONFIRMED) != 0;
        }
    }
    return false;
}

bool diag_has_critical_dtc(void) {
    if (diag_is_dtc_confirmed(DTC_P0217_ENGINE_COOLANT_OVERTEMP) ||
        diag_is_dtc_confirmed(DTC_P0563_SYSTEM_VOLTAGE_HIGH) ||
        diag_is_dtc_confirmed(DTC_P0121_TPS_RANGE_PERFORMANCE) ||
        diag_is_dtc_confirmed(DTC_P0606_ECU_INTERNAL_FAULT)) {
        return true;
    }
    return false;
}

bool diag_has_degraded_dtc(void) {
    if (diag_is_dtc_confirmed(DTC_P0115_ECT_CIRCUIT_MALFUNCTION) ||
        diag_is_dtc_confirmed(DTC_P0117_ECT_CIRCUIT_LOW) ||
        diag_is_dtc_confirmed(DTC_P0118_ECT_CIRCUIT_HIGH) ||
        diag_is_dtc_confirmed(DTC_P0120_TPS_CIRCUIT_MALFUNCTION) ||
        diag_is_dtc_confirmed(DTC_P0122_TPS_CIRCUIT_LOW) ||
        diag_is_dtc_confirmed(DTC_P0123_TPS_CIRCUIT_HIGH) ||
        diag_is_dtc_confirmed(DTC_P0105_MAP_CIRCUIT_MALFUNCTION) ||
        diag_is_dtc_confirmed(DTC_P0106_MAP_RANGE_PERFORMANCE) ||
        diag_is_dtc_confirmed(DTC_P0560_SYSTEM_VOLTAGE_MALFUNCTION) ||
        diag_is_dtc_confirmed(DTC_P0562_SYSTEM_VOLTAGE_LOW) ||
        diag_is_dtc_confirmed(DTC_U0100_LOST_COMM_ECM_GATEWAY)) {
        return true;
    }
    return false;
}

mil_status_t diag_calculate_mil_status(void) {
    if (diag_has_critical_dtc()) {
        return MIL_BLINKING;
    }
    if (diag_get_active_dtc_count() > 0) {
        return MIL_ON;
    }
    return MIL_OFF;
}

void diag_step(void) {
    s_diag_ticks++;
}
