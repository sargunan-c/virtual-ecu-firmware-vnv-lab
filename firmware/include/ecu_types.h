/**
 * @file ecu_types.h
 * @brief Automotive ECU Core Type Definitions and Data Structures
 * @standard ISO 26262 / C11 / AUTOSAR-inspired
 */

#ifndef ECU_TYPES_H
#define ECU_TYPES_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ECU_MAX_ACTIVE_DTCS         16
#define ECU_TICK_RATE_MS            10     /* 100 Hz main loop tick */
#define DTC_DEBOUNCE_CONFIRM_CYCLES 5      /* 50 ms debounce for qualification */
#define DTC_DEBOUNCE_HEAL_CYCLES    10     /* 100 ms debounce for recovery */

/* ECU Operating States */
typedef enum {
    ECU_STATE_OFF       = 0,
    ECU_STATE_INIT      = 1,
    ECU_STATE_STANDBY   = 2,
    ECU_STATE_RUNNING   = 3,
    ECU_STATE_DEGRADED  = 4,  /* Limp-home mode: reduced power, safe defaults */
    ECU_STATE_ERROR     = 5,  /* Emergency stop: fuel cutoff, engine halted */
    ECU_STATE_SHUTDOWN  = 6
} ecu_state_t;

/* Diagnostic Trouble Codes (OBD-II / ISO 14229 Standard) */
typedef enum {
    DTC_NONE                               = 0x0000,
    DTC_P0115_ECT_CIRCUIT_MALFUNCTION      = 0x0115,
    DTC_P0117_ECT_CIRCUIT_LOW              = 0x0117,
    DTC_P0118_ECT_CIRCUIT_HIGH             = 0x0118,
    DTC_P0217_ENGINE_COOLANT_OVERTEMP      = 0x0217,
    DTC_P0120_TPS_CIRCUIT_MALFUNCTION      = 0x0120,
    DTC_P0121_TPS_RANGE_PERFORMANCE        = 0x0121,
    DTC_P0122_TPS_CIRCUIT_LOW              = 0x0122,
    DTC_P0123_TPS_CIRCUIT_HIGH             = 0x0123,
    DTC_P0105_MAP_CIRCUIT_MALFUNCTION      = 0x0105,
    DTC_P0106_MAP_RANGE_PERFORMANCE        = 0x0106,
    DTC_P0560_SYSTEM_VOLTAGE_MALFUNCTION   = 0x0560,
    DTC_P0562_SYSTEM_VOLTAGE_LOW           = 0x0562,
    DTC_P0563_SYSTEM_VOLTAGE_HIGH          = 0x0563,
    DTC_P0606_ECU_INTERNAL_FAULT           = 0x0606,
    DTC_U0100_LOST_COMM_ECM_GATEWAY        = 0xC100
} dtc_code_t;

/* DTC Status Bitmask (ISO 14229 UDS compliant) */
#define DTC_STATUS_TEST_FAILED                  (1 << 0)
#define DTC_STATUS_TEST_FAILED_THIS_CYCLE       (1 << 1)
#define DTC_STATUS_PENDING                      (1 << 2)
#define DTC_STATUS_CONFIRMED                    (1 << 3)
#define DTC_STATUS_WARNING_INDICATOR_REQUESTED  (1 << 7)

/* Fault Injection Types */
typedef enum {
    FAULT_INJECT_NONE           = 0,
    FAULT_INJECT_SHORT_TO_GND   = 1,
    FAULT_INJECT_SHORT_TO_VCC   = 2,
    FAULT_INJECT_OPEN_CIRCUIT   = 3,
    FAULT_INJECT_STUCK_VALUE    = 4,
    FAULT_INJECT_ERRATIC_NOISE  = 5,
    FAULT_INJECT_CAN_TIMEOUT    = 6,
    FAULT_INJECT_TPS_MISMATCH   = 7
} fault_inject_type_t;

/* Target Sensors for Fault Injection */
typedef enum {
    TARGET_SENSOR_NONE      = 0,
    TARGET_SENSOR_ECT       = 1,
    TARGET_SENSOR_TPS       = 2,
    TARGET_SENSOR_MAP       = 3,
    TARGET_SENSOR_VBATT     = 4,
    TARGET_SENSOR_RPM       = 5,
    TARGET_COMM_CAN         = 6
} fault_target_t;

/* Actuator States */
typedef enum {
    FAN_OFF         = 0,
    FAN_LOW_SPEED   = 1,
    FAN_HIGH_SPEED  = 2
} fan_speed_t;

typedef enum {
    MIL_OFF         = 0,
    MIL_ON          = 1,
    MIL_BLINKING    = 2
} mil_status_t;

/* Sensor Physical Input Struct */
typedef struct {
    float    coolant_temp_c;          /* Engine Coolant Temp in °C: -40 to 150 */
    float    throttle_pos1_pct;       /* Primary Throttle 0.0 - 100.0% */
    float    throttle_pos2_pct;       /* Secondary Throttle (Cross-check): 100.0% - TPS1 */
    float    manifold_pressure_kpa;   /* MAP in kPa: 10 to 250 */
    float    battery_voltage_v;       /* Battery in Volts: 0 to 24 */
    uint16_t engine_rpm;              /* Engine RPM: 0 to 8000 */
    bool     ignition_switch;         /* Key Ignition: false = OFF, true = ON */
    bool     engine_crank_request;    /* Crank button: true = start cranking */
    bool     can_bus_connected;       /* CAN gateway alive signal */
} sensor_inputs_t;

/* Actuator Command Struct */
typedef struct {
    float        fuel_injection_pw_ms;    /* Injector pulse width (ms): 0.0 - 25.0 */
    float        ignition_timing_deg;     /* Spark advance (deg BTDC): 0.0 - 45.0 */
    fan_speed_t  cooling_fan_state;       /* Cooling fan mode */
    mil_status_t mil_lamp;                /* Check Engine Light */
    float        throttle_actuator_pct;   /* Commanded throttle plate % */
    bool         fuel_pump_relay;         /* Main fuel pump relay */
    bool         starter_relay_enable;    /* Starter solenoid lock */
} actuator_outputs_t;

/* DTC Storage Entry */
typedef struct {
    uint16_t dtc_code;
    uint8_t  status_mask;
    uint8_t  consecutive_fail_count;
    uint8_t  consecutive_pass_count;
    uint32_t first_fault_tick;
    uint32_t last_fault_tick;
} dtc_record_t;

/* Fault Injection Configuration */
typedef struct {
    fault_target_t      target;
    fault_inject_type_t type;
    float               fixed_value;
    bool                is_active;
    uint32_t            duration_ticks;
    uint32_t            elapsed_ticks;
} fault_injection_config_t;

/* Full ECU Telemetry Snapshot for Verification & Harness */
typedef struct {
    uint32_t            cycle_count;
    uint32_t            uptime_ms;
    ecu_state_t         current_state;
    ecu_state_t         previous_state;
    sensor_inputs_t     raw_inputs;
    sensor_inputs_t     filtered_inputs;
    actuator_outputs_t  actuators;
    uint8_t             active_dtc_count;
    uint16_t            active_dtcs[ECU_MAX_ACTIVE_DTCS];
    bool                limp_home_active;
    bool                emergency_stop_active;
    uint32_t            can_timeout_counter;
    bool                post_passed;
} ecu_telemetry_t;

#ifdef __cplusplus
}
#endif

#endif /* ECU_TYPES_H */
