"""
Test Suite: Sensor Input Validation & Plausibility
Tests ECT warm-up enrichment under controlled operating points,
cooling fan activation thresholds with cooling-down hysteresis,
and dual-channel throttle potentiometer correlation validation.
"""

from framework.harness.ecu_adapter import EcuState, FanSpeed, DtcCode

def test_cold_start_fuel_enrichment(ecu):
    """
    Verify coolant temperature below 60°C commands richer fuel injection pulse width.
    Operating conditions are held identical (RPM=1200, MAP=80.0 kPa, TPS=15.0%)
    to isolate the coolant enrichment factor.
    """
    # 1. Cold engine at 20°C
    ecu.boot_to_running(rpm=1200)
    ecu.set_inputs(coolant_temp_c=20.0, rpm=1200, map_kpa=80.0, tps_pct=15.0)
    ecu.step(2)
    cold_telem = ecu.get_telemetry()

    # 2. Warm engine at 85°C with identical load and speed
    ecu.set_inputs(coolant_temp_c=85.0, rpm=1200, map_kpa=80.0, tps_pct=15.0)
    ecu.step(2)
    warm_telem = ecu.get_telemetry()

    cold_pw = cold_telem["actuators"]["fuel_pw_ms"]
    warm_pw = warm_telem["actuators"]["fuel_pw_ms"]

    assert cold_pw > warm_pw, f"Cold PW ({cold_pw} ms) should exceed warm PW ({warm_pw} ms)"

def test_cooling_fan_activation_and_hysteresis(ecu):
    """
    Verify cooling fan activation thresholds and cooling-down hysteresis:
    - Below 95°C: OFF
    - 95°C to 104°C: LOW_SPEED
    - >= 105°C: HIGH_SPEED
    - Cooling down:
      - Drops below 105°C (100°C) -> LOW_SPEED
      - Between 89°C and 94°C (92°C) -> LOW_SPEED (hysteresis holds)
      - <= 88°C (87°C) -> OFF
    """
    ecu.boot_to_running(rpm=1200)

    # 1. Nominal operating temp (85°C) -> Fan OFF
    ecu.set_inputs(coolant_temp_c=85.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.OFF

    # 2. Temperature rises to 97°C (>= 95°C) -> Fan LOW
    ecu.set_inputs(coolant_temp_c=97.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.LOW

    # 3. Temperature reaches overheat warning (106°C >= 105°C) -> Fan HIGH
    ecu.set_inputs(coolant_temp_c=106.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.HIGH

    # 4. Hysteresis cool-down: drop to 100°C -> drops to LOW
    ecu.set_inputs(coolant_temp_c=100.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.LOW

    # 5. Hysteresis cool-down: drop to 92°C (> 88°C threshold) -> remains LOW
    ecu.set_inputs(coolant_temp_c=92.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.LOW, "Fan should remain LOW due to hysteresis"

    # 6. Drop to 87°C (<= 88°C hysteresis lower cutoff) -> turns OFF
    ecu.set_inputs(coolant_temp_c=87.0)
    ecu.step(2)
    assert ecu.get_telemetry()["actuators"]["fan_state"] == FanSpeed.OFF, "Fan must turn OFF when temp <= 88°C"

def test_dual_throttle_correlation_valid(ecu):
    """Verify dual channel throttle signals correlate correctly when sum equals 100%."""
    ecu.boot_to_running(rpm=1500)

    # Commanded 30%, TPS2 = 70% (Sum = 100%, deviation = 0% <= 7%)
    ecu.set_inputs(tps_pct=30.0, tps2_pct=70.0)
    ecu.step(3)

    assert not ecu.is_dtc_active(DtcCode.P0121_TPS_RANGE_PERFORMANCE)
    assert ecu.get_state() == EcuState.RUNNING

def test_dual_throttle_correlation_invalid_detection(ecu):
    """
    Verify invalid TPS correlation handling:
    TPS1 = 30%, TPS2 = 50% -> Sum = 80%, error = 20% (> 7% tolerance).
    Must qualify DTC P0121 and transition to ERROR state.
    """
    ecu.boot_to_running(rpm=1500)

    ecu.set_inputs(tps_pct=30.0, tps2_pct=50.0)
    ecu.step(6)

    assert ecu.is_dtc_active(DtcCode.P0121_TPS_RANGE_PERFORMANCE)
    assert ecu.get_state() == EcuState.ERROR
