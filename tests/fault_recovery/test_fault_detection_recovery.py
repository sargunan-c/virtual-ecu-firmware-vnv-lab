"""
Test Suite: Fault Detection, Isolation, and Recovery (FDIR)
Validates fault qualification debounce, fail-safe state machine transitions,
emergency stop fuel cut-off, and self-healing recovery.
"""

from framework.harness.ecu_adapter import EcuState, DtcCode, FanSpeed, MilLamp
from simulation.fault_injection.fault_injector import FaultTarget

def test_ect_short_gnd_fault_qualification_and_recovery(ecu, fault_injector):
    """
    Simulates ECT wiring short to ground (-45°C).
    Validates:
      1. Debounce qualification of DTC P0117.
      2. Transition from RUNNING to DEGRADED (Limp-Home).
      3. Fallback safe temperature applied (85.0°C).
      4. Clearing fault allows consecutive clean cycles to heal DTC and restore RUNNING.
    """
    ecu.boot_to_running(rpm=1500)
    assert ecu.get_state() == EcuState.RUNNING

    # Inject Short to GND on ECT sensor
    fault_injector.inject_sensor_short_gnd(FaultTarget.ECT)

    # Step debounce confirmation cycles (5 ticks)
    ecu.step(5)

    assert ecu.is_dtc_active(DtcCode.P0117_ECT_CIRCUIT_LOW), "DTC P0117 must be confirmed after debounce"
    assert ecu.get_state() == EcuState.DEGRADED, "ECU must enter DEGRADED mode on sensor failure"

    telem = ecu.get_telemetry()
    assert telem["actuators"]["mil_lamp"] == MilLamp.ON, "MIL lamp must be illuminated in Limp mode"
    # Verify fallback coolant temperature was used for engine safety
    assert telem["inputs"]["coolant_temp_c"] == 85.0, "ECU should use 85°C fallback default"

    # RECOVERY PHASE: Clear fault
    fault_injector.clear_target_fault(FaultTarget.ECT)

    # Step through healing debounce cycles (10 ticks)
    ecu.step(11)

    assert not ecu.is_dtc_active(DtcCode.P0117_ECT_CIRCUIT_LOW), "DTC P0117 should heal after clean cycles"
    assert ecu.get_state() == EcuState.RUNNING, "ECU should recover from DEGRADED to RUNNING"
    assert ecu.get_telemetry()["actuators"]["mil_lamp"] == MilLamp.OFF, "MIL lamp should extinguish"

def test_asil_b_dual_tps_mismatch_emergency_stop(ecu, fault_injector):
    """
    Simulates TPS2 potentiometer drift/desynchronization.
    In ASIL-B architecture, dual throttle mismatch indicates potential unintended acceleration.
    Validates:
      1. Qualification of DTC P0121 (TPS Range/Performance).
      2. Fail-safe transition to ERROR (Emergency Stop).
      3. Fuel injection cut-off (0.0 ms) and spark advance kill (0.0 deg).
      4. Check Engine Light (MIL) blinking in warning mode.
    """
    ecu.boot_to_running(rpm=2500)
    assert ecu.get_state() == EcuState.RUNNING

    # Corrupt TPS2 value: commanded TPS1 is 20%, expected TPS2 is 80%, inject 20%
    # Sum = 40% (Deviation of 60% > 7% tolerance)
    fault_injector.inject_tps_correlation_failure(corrupted_tps2_val=20.0)

    ecu.step(5)

    assert ecu.is_dtc_active(DtcCode.P0121_TPS_RANGE_PERFORMANCE), "DTC P0121 must be confirmed"
    assert ecu.get_state() == EcuState.ERROR, "ECU must transition to ERROR state on TPS mismatch"

    telem = ecu.get_telemetry()
    assert telem["actuators"]["fuel_pw_ms"] == 0.0, "Fuel must be cut off in EMERGENCY STOP"
    assert telem["actuators"]["ignition_timing_deg"] == 0.0, "Ignition must be killed in EMERGENCY STOP"
    assert telem["actuators"]["mil_lamp"] == MilLamp.BLINKING, "MIL lamp must blink for critical fault"
    assert telem["actuators"]["cooling_fan_state"] == FanSpeed.HIGH, "Cooling fan must run at HIGH speed"

def test_critical_thermal_overheat_emergency_stop(ecu, fault_injector):
    """
    Simulates severe coolant boiling / radiator puncture (>118°C).
    Validates:
      1. Qualification of DTC P0217 (Engine Coolant Over-temperature).
      2. Emergency stop state transition.
      3. Maximum cooling fan activation to prevent thermal engine seizure.
    """
    ecu.boot_to_running(rpm=1800)
    assert ecu.get_state() == EcuState.RUNNING

    # Inject 125°C critical overheat
    fault_injector.inject_stuck_value(FaultTarget.ECT, 125.0)

    ecu.step(5)

    assert ecu.is_dtc_active(DtcCode.P0217_ENGINE_COOLANT_OVERTEMP)
    assert ecu.get_state() == EcuState.ERROR

    telem = ecu.get_telemetry()
    assert telem["actuators"]["cooling_fan_state"] == FanSpeed.HIGH
    assert telem["actuators"]["fuel_pw_ms"] == 0.0

def test_can_communication_timeout_and_recovery(ecu, fault_injector):
    """
    Simulates lost CAN bus communication with vehicle gateway.
    Validates:
      1. DTC U0100 qualification.
      2. Limp-home mode entry with throttle derated to 25%.
      3. Recovery when CAN heartbeat resumes.
    """
    ecu.boot_to_running(rpm=1800)
    assert ecu.get_state() == EcuState.RUNNING

    # Inject CAN Bus Off
    fault_injector.inject_can_bus_off()

    ecu.step(5)

    assert ecu.is_dtc_active(DtcCode.U0100_LOST_COMM_ECM_GATEWAY)
    assert ecu.get_state() == EcuState.DEGRADED

    telem = ecu.get_telemetry()
    # Commanded throttle in Limp-home must be capped at 25%
    assert telem["actuators"]["throttle_cmd_pct"] <= 25.0

    # Restore CAN bus
    fault_injector.clear_target_fault(FaultTarget.CAN)
    ecu.step(11)

    assert not ecu.is_dtc_active(DtcCode.U0100_LOST_COMM_ECM_GATEWAY)
    assert ecu.get_state() == EcuState.RUNNING

def test_map_sensor_fault_injection_and_fallback(ecu, fault_injector):
    """
    Simulates MAP sensor short to VCC (260 kPa).
    Validates DTC P0106 qualification and fallback to default atmospheric pressure (101.3 kPa).
    """
    ecu.boot_to_running(rpm=1500)
    fault_injector.inject_sensor_short_vcc(FaultTarget.MAP)

    ecu.step(5)

    assert ecu.is_dtc_active(DtcCode.P0106_MAP_RANGE_PERFORMANCE)
    assert ecu.get_state() == EcuState.DEGRADED

    telem = ecu.get_telemetry()
    assert telem["inputs"]["map_kpa"] == 101.3, "Filtered MAP must fall back to 101.3 kPa"

    # Clear fault and verify healing
    fault_injector.clear_target_fault(FaultTarget.MAP)
    ecu.step(11)

    assert not ecu.is_dtc_active(DtcCode.P0106_MAP_RANGE_PERFORMANCE)
    assert ecu.get_state() == EcuState.RUNNING
