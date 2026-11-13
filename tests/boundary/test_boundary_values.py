"""
Test Suite: Boundary Value Testing (BVT)
Rigorous boundary value analysis on sensor inputs, thresholds, and guard conditions.
"""

from framework.harness.ecu_adapter import EcuState, DtcCode, FanSpeed

def test_ect_lower_valid_boundary(ecu):
    """ECT at -39.0°C must be accepted without circuit low DTC."""
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=-39.0)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0117_ECT_CIRCUIT_LOW)

def test_ect_below_lower_boundary_triggers_fault(ecu):
    """ECT at -40.0°C (below -39.0°C) must trigger DTC P0117 Circuit Low."""
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=-40.0)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0117_ECT_CIRCUIT_LOW)
    # ECU should enter Limp-Home (DEGRADED) mode
    assert ecu.get_state() == EcuState.DEGRADED

def test_ect_upper_valid_boundary(ecu):
    """ECT at 139.0°C is within maximum range threshold before sensor disconnect fault."""
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=139.0)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0118_ECT_CIRCUIT_HIGH)

def test_ect_above_upper_boundary_triggers_circuit_high(ecu):
    """ECT at 140.0°C triggers DTC P0118 Circuit High."""
    ecu.boot_to_running()
    ecu.set_inputs(coolant_temp_c=140.0)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0118_ECT_CIRCUIT_HIGH)

def test_ect_overheat_critical_boundary(ecu):
    """ECT at 118.0°C crosses critical thermal limit, triggering DTC P0217 and Emergency Stop."""
    ecu.boot_to_running()
    # At 117.0°C: not critical
    ecu.set_inputs(coolant_temp_c=117.0)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0217_ENGINE_COOLANT_OVERTEMP)

    # Step to 118.5°C: Critical threshold crossed
    ecu.set_inputs(coolant_temp_c=118.5)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0217_ENGINE_COOLANT_OVERTEMP)
    assert ecu.get_state() == EcuState.ERROR

def test_battery_voltage_boundaries(ecu):
    """Test lower boundary (8.5V) and upper boundary (16.5V) of vehicle electrical system."""
    ecu.boot_to_running()

    # Just above lower boundary: 8.6V -> Nominal
    ecu.set_inputs(battery_voltage_v=8.6)
    ecu.step(6)
    assert not ecu.is_dtc_active(DtcCode.P0562_SYSTEM_VOLTAGE_LOW)

    # Drop below boundary: 8.4V -> Undervoltage fault
    ecu.set_inputs(battery_voltage_v=8.4)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0562_SYSTEM_VOLTAGE_LOW)

    # Upper boundary test: 16.6V -> Overvoltage fault
    ecu.clear_diagnostics()
    ecu.set_inputs(battery_voltage_v=16.6)
    ecu.step(6)
    assert ecu.is_dtc_active(DtcCode.P0563_SYSTEM_VOLTAGE_HIGH)

def test_throttle_limits_and_clamping(ecu):
    """Verify throttle position 0% and 100% boundary limits."""
    ecu.boot_to_running()

    # Minimum throttle (0.0%)
    ecu.set_inputs(tps_pct=0.0, tps2_pct=100.0)
    ecu.step(3)
    assert ecu.get_telemetry()["actuators"]["throttle_cmd_pct"] == 0.0

    # Wide Open Throttle (100.0%)
    ecu.set_inputs(tps_pct=100.0, tps2_pct=0.0)
    ecu.step(3)
    assert ecu.get_telemetry()["actuators"]["throttle_cmd_pct"] == 100.0

