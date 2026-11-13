/**
 * @file ecu_diagnostics.h
 * @brief Diagnostic Trouble Code (DTC) Management & ISO 14229 / OBD-II Services
 */

#ifndef ECU_DIAGNOSTICS_H
#define ECU_DIAGNOSTICS_H

#include "ecu_types.h"

#ifdef __cplusplus
extern "C" {
#endif

void diag_init(void);
void diag_report_fault(dtc_code_t dtc, bool is_failing);
void diag_clear_all_dtcs(void);
uint8_t diag_get_active_dtc_count(void);
void diag_get_active_dtcs(uint16_t *out_dtcs, uint8_t max_count);
bool diag_is_dtc_confirmed(dtc_code_t dtc);
bool diag_has_critical_dtc(void);
bool diag_has_degraded_dtc(void);
mil_status_t diag_calculate_mil_status(void);
void diag_step(void);

#ifdef __cplusplus
}
#endif

#endif /* ECU_DIAGNOSTICS_H */

