"""
Test Suite: Negative Testing
Validates error handling, out-of-bounds inputs, invalid state transitions, and starter lockouts.
"""

from framework.harness.ecu_adapter import EcuState, DtcCode

def test_negative_throttle_input_triggers_circuit_low(ecu):
    """Negative throttle position (-5.0%) represents electrical short to ground."""
    ecu.boot_to_running()
    ecu.set_inputs(tps_pct=-5.0, tps2_pct=105.0)
    ecu.step(6)

    assert ecu.is_dtc_active(DtcCode.P0122_TPS_CIRCUIT_LOW)
    # Output throttle command must be clamped safely to 0%
    assert ecu.get_telemetry()["actuators"]["throttle_cmd_pct"] == 0.0

def test_over_range_throttle_input_triggers_circuit_high(ecu):
    """Throttle position > 100% (e.g. 115%) represents short to VCC."""
    ecu.boot_to_running()
    ecu.set_inputs(tps_pct=115.0, tps2_pct=0.0)
    ecu.step(6)

    assert ecu.is_dtc_active(DtcCode.P0123_TPS_CIRCUIT_HIGH)

def test_starter_lockout_while_engine_running(ecu):
    """Safety Interlock: Starter motor relay must NOT engage if engine is already running."""
    ecu.boot_to_running(rpm=2000)
    assert ecu.get_state() == EcuState.RUNNING

    # Attempt to request starter crank while engine is revving
    ecu.set_inputs(rpm=2000, crank=True)
    ecu.step(2)

    telem = ecu.get_telemetry()
    assert telem["actuators"]["starter_enable"] is False, "Starter must remain locked out while running"

def test_zero_voltage_electrical_collapse(ecu):
    """Sudden complete drop to 0V battery voltage."""
    ecu.boot_to_running()
    ecu.set_inputs(battery_voltage_v=0.0)
    ecu.step(6)

    assert ecu.is_dtc_active(DtcCode.P0562_SYSTEM_VOLTAGE_LOW)
    assert ecu.get_state() == EcuState.DEGRADED

def test_invalid_state_transition_no_crank_without_ignition(ecu):
    """Crank button pressed while ignition switch is OFF must NOT start engine."""
    ecu.set_inputs(ignition=False, crank=True, rpm=300)
    ecu.step(5)

    assert ecu.get_state() == EcuState.OFF
    assert ecu.get_telemetry()["actuators"]["fuel_pw_ms"] == 0.0

