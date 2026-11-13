"""
Test Suite: Boundary Value Testing (BVT)
Rigorous boundary value analysis on sensor inputs, thresholds, and guard conditions
against exact firmware calibration constants.
"""

from framework.harness.ecu_adapter import EcuState, DtcCode

def test_ect_lower_valid_boundary(ecu):
    """ECT at -39.0°C (exact lower limit) must be accepted with no DTC and state RUNNING."""
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=-39.0)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0117_ECT_CIRCUIT_LOW)
    assert ecu.get_state() == EcuState.RUNNING

def test_ect_below_lower_boundary_triggers_fault(ecu):
    """ECT at -40.0°C (below -39.0°C threshold) must trigger DTC P0117 and enter DEGRADED."""
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=-40.0)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0117_ECT_CIRCUIT_LOW)
    assert ecu.get_state() == EcuState.DEGRADED

def test_ect_upper_valid_boundary(ecu):
    """
    ECT at 139.0°C is within maximum electrical sensor range before P0118 circuit high.
    Verifies that DTC P0118 is NOT active, while thermal protection (P0217) safely enforces ERROR.
    """
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=139.0)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0118_ECT_CIRCUIT_HIGH)
    # Severe thermal condition (>118°C) triggers critical safety state
    assert ecu.is_dtc_active(DtcCode.P0217_ENGINE_COOLANT_OVERTEMP)
    assert ecu.get_state() == EcuState.ERROR

def test_ect_above_upper_boundary_triggers_circuit_high(ecu):
    """ECT at 140.0°C (above 139.0°C electrical limit) triggers DTC P0118 Circuit High."""
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=140.0)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0118_ECT_CIRCUIT_HIGH)
    assert ecu.get_state() == EcuState.ERROR

def test_ect_overheat_critical_boundary(ecu):
    """ECT at 118.0°C crosses critical thermal limit, triggering DTC P0217 and Emergency Stop."""
    ecu.boot_to_running()
    # At 117.0°C: warning range, not critical
    ecu.set_inputs(coolant_temp_c=117.0)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0217_ENGINE_COOLANT_OVERTEMP)
    assert ecu.get_state() == EcuState.RUNNING

    # Step to 118.5°C: Critical threshold crossed (ECT_OVERHEAT_CRITICAL_C = 118.0°C)
    ecu.set_inputs(coolant_temp_c=118.5)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0217_ENGINE_COOLANT_OVERTEMP)
    assert ecu.get_state() == EcuState.ERROR

def test_battery_voltage_boundaries(ecu):
    """Test lower boundary (8.5V) and upper boundary (16.5V) against exact firmware calibration."""
    ecu.boot_to_running()

    # Just above lower boundary: 8.6V -> Nominal
    ecu.set_inputs(battery_voltage_v=8.6)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0562_SYSTEM_VOLTAGE_LOW)
    assert ecu.get_state() == EcuState.RUNNING

    # Drop below boundary: 8.4V (< 8.5V threshold) -> Undervoltage fault and DEGRADED state
    ecu.set_inputs(battery_voltage_v=8.4)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0562_SYSTEM_VOLTAGE_LOW)
    assert ecu.get_state() == EcuState.DEGRADED

    # Upper boundary test: 16.6V (> 16.5V threshold) -> Critical Overvoltage fault and ERROR state
    ecu.clear_diagnostics()
    ecu.boot_to_running()
    ecu.set_inputs(battery_voltage_v=16.6)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0563_SYSTEM_VOLTAGE_HIGH)
    assert ecu.get_state() == EcuState.ERROR

def test_throttle_limits_and_clamping(ecu):
    """Verify throttle position 0% and 100% boundary limits produce valid outputs without fault."""
    ecu.boot_to_running()

    # Minimum throttle (0.0%)
    ecu.set_inputs(tps_pct=0.0, tps2_pct=100.0)
    ecu.step(3)
    assert ecu.get_telemetry()["actuators"]["throttle_cmd_pct"] == 0.0
    assert not ecu.is_dtc_active(DtcCode.P0120_TPS_CIRCUIT_MALFUNCTION)
    assert ecu.get_state() == EcuState.RUNNING

    # Wide Open Throttle (100.0%)
    ecu.set_inputs(tps_pct=100.0, tps2_pct=0.0)
    ecu.step(3)
    assert ecu.get_telemetry()["actuators"]["throttle_cmd_pct"] == 100.0
    assert not ecu.is_dtc_active(DtcCode.P0120_TPS_CIRCUIT_MALFUNCTION)
    assert ecu.get_state() == EcuState.RUNNING
