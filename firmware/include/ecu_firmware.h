/**
 * @file ecu_firmware.h
 * @brief Virtual ECU Firmware Top-Level Harness & Verification API
 */

#ifndef ECU_FIRMWARE_H
#define ECU_FIRMWARE_H

#include "ecu_types.h"
#include "ecu_diagnostics.h"
#include "ecu_sensors.h"
#include "ecu_actuators.h"
#include "ecu_state_machine.h"
#include "ecu_fault_injection.h"

#ifdef _WIN32
    #ifdef BUILDING_ECU_DLL
        #define ECU_API __declspec(dllexport)
    #elif defined(ECU_USE_DLL)
        #define ECU_API __declspec(dllimport)
    #else
        #define ECU_API
    #endif
#else
    #define ECU_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

ECU_API void ecu_init(void);
ECU_API void ecu_reset(void);
ECU_API void ecu_set_inputs(const sensor_inputs_t *inputs);
ECU_API void ecu_get_inputs(sensor_inputs_t *inputs);
ECU_API void ecu_step(uint32_t step_count);
ECU_API void ecu_get_telemetry(ecu_telemetry_t *telemetry);
ECU_API ecu_state_t ecu_get_state(void);
ECU_API void ecu_inject_fault(uint8_t target, uint8_t type, float fixed_value, uint32_t duration_ticks);
ECU_API void ecu_clear_fault(uint8_t target);
ECU_API void ecu_clear_all_faults(void);
ECU_API void ecu_clear_diagnostics(void);
ECU_API bool ecu_is_dtc_active(uint16_t dtc);
ECU_API uint8_t ecu_get_active_dtc_count(void);
ECU_API void ecu_get_active_dtc_list(uint16_t *dtc_list, uint8_t max_count);

#ifdef __cplusplus
}
#endif

#endif /* ECU_FIRMWARE_H */
