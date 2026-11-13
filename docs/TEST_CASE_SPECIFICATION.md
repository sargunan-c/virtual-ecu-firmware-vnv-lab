# Test Case Specification

## Complete Test Case Catalog & SRS Traceability

**Total Test Cases:** 25  
**Current Test Status:** 25 / 25 PASSED (100% Success Rate)  

---

### Test Case Catalog

| Test ID | Test Function | Category | SRS Requirement | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-001** | `test_ect_lower_valid_boundary` | Boundary | `REQ-BVT-001` | ECT at -39.0°C accepted; no DTC | **PASS** |
| **TC-002** | `test_ect_below_lower_boundary_triggers_fault` | Boundary | `REQ-BVT-002` | ECT at -40.0°C qualifies DTC P0117 -> Limp-Home | **PASS** |
| **TC-003** | `test_ect_upper_valid_boundary` | Boundary | `REQ-BVT-003` | ECT at 139.0°C accepted; no DTC | **PASS** |
| **TC-004** | `test_ect_above_upper_boundary_triggers_circuit_high` | Boundary | `REQ-BVT-004` | ECT at 140.0°C qualifies DTC P0118 | **PASS** |
| **TC-005** | `test_ect_overheat_critical_boundary` | Boundary | `REQ-BVT-005` | ECT at 118.5°C qualifies DTC P0217 -> Emergency Stop | **PASS** |
| **TC-006** | `test_battery_voltage_boundaries` | Boundary | `REQ-BVT-006` | 8.4V qualifies P0562; 16.6V qualifies P0563 | **PASS** |
| **TC-007** | `test_throttle_limits_and_clamping` | Boundary | `REQ-BVT-007` | 0% and 100% throttle commands correctly clamped | **PASS** |
| **TC-008** | `test_ect_short_gnd_fault_qualification_and_recovery` | Fault Recovery | `REQ-FDIR-001` | Short to GND -> DTC P0117 confirmed -> Heal to RUNNING | **PASS** |
| **TC-009** | `test_asil_b_dual_tps_mismatch_emergency_stop` | Fault Recovery | `REQ-FDIR-002` | Dual TPS deviation >7% -> P0121 -> Emergency Stop | **PASS** |
| **TC-010** | `test_critical_thermal_overheat_emergency_stop` | Fault Recovery | `REQ-FDIR-003` | 125°C overheat -> P0217 -> Fuel cutoff, High Fan | **PASS** |
| **TC-011** | `test_can_communication_timeout_and_recovery` | Fault Recovery | `REQ-FDIR-004` | CAN loss -> DTC U0100 -> Restored -> Recovery | **PASS** |
| **TC-012** | `test_map_sensor_fault_injection_and_fallback` | Fault Recovery | `REQ-FDIR-005` | MAP >245 kPa -> P0106 -> Limp fallback to 101.3 kPa | **PASS** |
| **TC-013** | `test_ecu_initial_state_off` | Functional | `REQ-FSM-001` | Reset with ignition OFF -> State OFF | **PASS** |
| **TC-014** | `test_ecu_power_on_and_post_sequence` | Functional | `REQ-FSM-002` | Ignition ON -> POST (30ms) -> State STANDBY | **PASS** |
| **TC-015** | `test_engine_cranking_to_running` | Functional | `REQ-FSM-003` | Cranking above 450 RPM -> State RUNNING | **PASS** |
| **TC-016** | `test_fuel_injection_and_spark_advance_dynamics` | Functional | `REQ-ACT-001` | Injection PW and spark advance scale with MAP & RPM | **PASS** |
| **TC-017** | `test_graceful_shutdown_on_ignition_off` | Functional | `REQ-FSM-004` | Ignition OFF -> State SHUTDOWN -> State OFF | **PASS** |
| **TC-018** | `test_cold_start_fuel_enrichment` | Sensors | `REQ-SENS-001` | Temp < 60°C commands richer pulse width | **PASS** |
| **TC-019** | `test_cooling_fan_activation_thresholds` | Sensors | `REQ-ACT-002` | Fan OFF (<90°C), LOW (≥95°C), HIGH (≥105°C) | **PASS** |
| **TC-020** | `test_dual_throttle_correlation_valid` | Sensors | `REQ-SENS-002` | Correlated TPS1 + TPS2 = 100% passes without DTC | **PASS** |
| **TC-021** | `test_negative_throttle_input_triggers_circuit_low` | Negative | `REQ-NEG-001` | -5.0% throttle input qualifies DTC P0122 & clamps to 0% | **PASS** |
| **TC-022** | `test_over_range_throttle_input_triggers_circuit_high` | Negative | `REQ-NEG-002` | 115% throttle input qualifies DTC P0123 & clamps | **PASS** |
| **TC-023** | `test_starter_lockout_while_engine_running` | Negative | `REQ-NEG-003` | Starter crank request while running is locked out | **PASS** |
| **TC-024** | `test_zero_voltage_electrical_collapse` | Negative | `REQ-NEG-004` | Sudden 0V battery drop qualifies undervoltage | **PASS** |
| **TC-025** | `test_invalid_state_transition_no_crank_without_ignition` | Negative | `REQ-NEG-005` | Cranking without ignition remains in OFF state | **PASS** |
