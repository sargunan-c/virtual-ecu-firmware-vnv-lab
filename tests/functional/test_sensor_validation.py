"""
Test Suite: Sensor Input Validation & Plausibility
Tests ECT warm-up enrichment, dual-channel throttle potentiometer correlation, and cooling fan hysteresis.
"""

from framework.harness.ecu_adapter import EcuState, FanSpeed, MilLamp, DtcCode

def test_cold_start_fuel_enrichment(ecu):
    """Verify coolant temperature below 60°C commands richer fuel injection pulse width."""
    # Running at 20°C (Cold)
    ecu.boot_to_running(rpm=1200)
    ecu.set_inputs(coolant_temp_c=20.0, rpm=1200, map_kpa=80.0)
    ecu.step(2)
    cold_telem = ecu.get_telemetry()

    # Running at 85°C (Warm nominal)
    ecu.set_inputs(coolant_temp_c=85.0, rpm=1200, map_kpa=80.0)
    ecu.step(2)
    warm_telem = ecu.get_telemetry()

    cold_pw = cold_telem["actuators"]["fuel_pw_ms"]
    warm_pw = warm_telem["actuators"]["fuel_pw_ms"]

    assert cold_pw > warm_pw, f"Cold PW ({cold_pw} ms) should exceed warm PW ({warm_pw} ms)"

def test_cooling_fan_activation_thresholds(ecu):
    """Verify cooling fan switches from OFF -> LOW_SPEED (>=95°C) -> HIGH_SPEED (>=105°C)."""
    ecu.boot_to_running(rpm=1200)

    # 1. Nominal operating temp (85°C) -> Fan OFF
    ecu.set_inputs(coolant_temp_c=85.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.OFF

    # 2. Temperature rises to 97°C -> Fan LOW
    ecu.set_inputs(coolant_temp_c=97.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.LOW

    # 3. Temperature reaches overheat warning (106°C) -> Fan HIGH
    ecu.set_inputs(coolant_temp_c=106.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.HIGH

def test_dual_throttle_correlation_valid(ecu):
    """Verify dual channel throttle signals correlate correctly when sum equals 100%."""
    ecu.boot_to_running(rpm=1500)

    # Commanded 30%, TPS2 = 70%
    ecu.set_inputs(tps_pct=30.0, tps2_pct=70.0)
    ecu.step(3)

    assert not ecu.is_dtc_active(DtcCode.P0121_TPS_RANGE_PERFORMANCE)
    assert ecu.get_state() == EcuState.RUNNING

