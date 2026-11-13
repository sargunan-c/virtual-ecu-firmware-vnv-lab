/**
 * @file ecu_sensors.h
 * @brief Automotive Sensor Processing, Boundary Validation & Plausibility Checks
 */

#ifndef ECU_SENSORS_H
#define ECU_SENSORS_H

#include "ecu_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Calibration Thresholds */
#define ECT_MIN_VALID_C           (-39.0f)
#define ECT_MAX_VALID_C           (139.0f)
#define ECT_OVERHEAT_WARNING_C    (105.0f)
#define ECT_OVERHEAT_CRITICAL_C   (118.0f)
#define ECT_FALLBACK_DEFAULT_C    (85.0f)

#define TPS_MIN_VALID_PCT         (0.0f)
#define TPS_MAX_VALID_PCT         (100.0f)
#define TPS_DUAL_MAX_TOLERANCE    (7.0f)    /* Dual channel plausibility max error % */

#define MAP_MIN_VALID_KPA         (15.0f)
#define MAP_MAX_VALID_KPA         (245.0f)
#define MAP_FALLBACK_DEFAULT_KPA  (101.3f)

#define VBATT_MIN_VALID_V         (8.5f)
#define VBATT_MAX_VALID_V         (16.5f)
#define VBATT_CRITICAL_LOW_V      (6.5f)
#define VBATT_CRITICAL_HIGH_V     (18.0f)

#define RPM_MAX_REDLINE           (6800)
#define RPM_CRANKING_THRESHOLD    (450)

void sensors_init(void);
void sensors_process(const sensor_inputs_t *raw_in, sensor_inputs_t *filtered_out);
bool sensors_are_plausible(void);

#ifdef __cplusplus
}
#endif

#endif /* ECU_SENSORS_H */

