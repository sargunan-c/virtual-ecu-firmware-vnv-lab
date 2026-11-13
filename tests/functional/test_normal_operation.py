"""
Test Suite: Normal ECU Operation & Operating State Transitions
Validates power states, startup POST, standby, running, and controlled shutdown.
"""

from framework.harness.ecu_adapter import EcuState

def test_ecu_initial_state_off(ecu):
    """Verify ECU is in OFF state immediately after hardware reset without ignition."""
    ecu.set_inputs(ignition=False, rpm=0)
    ecu.step(1)
    telemetry = ecu.get_telemetry()

    assert telemetry["state_name"] == "OFF", f"Expected OFF but got {telemetry['state_name']}"
    assert telemetry["actuators"]["fuel_pw_ms"] == 0.0
    assert telemetry["actuators"]["fuel_pump"] is False
    assert telemetry["actuators"]["starter_enable"] is False

def test_ecu_power_on_and_post_sequence(ecu):
    """Verify Ignition ON triggers INIT -> POST (30 ms) -> STANDBY."""
    ecu.set_inputs(ignition=True, rpm=0, coolant_temp_c=25.0)
    
    # Tick 1: Transition OFF -> INIT
    ecu.step(1)
    assert ecu.get_state() == EcuState.INIT, f"Expected INIT on tick 1, got {ecu.get_state_name()}"

    # Ticks 2-4: POST self-check completion
    ecu.step(3)
    assert ecu.get_state() == EcuState.STANDBY, f"Expected STANDBY after POST, got {ecu.get_state_name()}"

    telem = ecu.get_telemetry()
    assert telem["actuators"]["fuel_pump"] is True, "Fuel pump should prime in STANDBY"
    assert telem["actuators"]["starter_enable"] is True, "Starter should be enabled in STANDBY with zero RPM"

def test_engine_cranking_to_running(ecu):
    """
    Verify cranking threshold boundary:
    Cranks at 400 RPM (< 450 RPM threshold) -> remains in STANDBY.
    Cranks at 460 RPM (>= 450 RPM threshold) -> transitions to RUNNING.
    """
    ecu.set_inputs(ignition=True, rpm=0)
    ecu.step(4)  # Arrive in STANDBY
    assert ecu.get_state() == EcuState.STANDBY

    # Sub-threshold cranking: 400 RPM
    ecu.set_inputs(ignition=True, rpm=400, crank=True)
    ecu.step(2)
    assert ecu.get_state() == EcuState.STANDBY, "RPM 400 (< 450 threshold) must remain in STANDBY"

    # Above-threshold cranking: 460 RPM
    ecu.set_inputs(ignition=True, rpm=460, crank=True)
    ecu.step(1)
    assert ecu.get_state() == EcuState.RUNNING, "RPM 460 must transition to RUNNING"

    telem = ecu.get_telemetry()
    assert telem["actuators"]["starter_enable"] is False, "Starter must disengage once engine runs"
    assert telem["actuators"]["fuel_pw_ms"] > 0.0, "Fuel injection pulse width must be positive"

def test_fuel_injection_and_spark_advance_dynamics(ecu):
    """
    Verify independent effects of MAP and RPM:
    1. Varying MAP at constant RPM changes fuel pulse width while spark timing remains constant.
    2. Varying RPM at constant MAP increases spark advance.
    """
    ecu.boot_to_running(rpm=1500)

    # 1. Test load response at constant RPM (1500 RPM, 85°C)
    ecu.set_inputs(rpm=1500, map_kpa=40.0, tps_pct=15.0, coolant_temp_c=85.0)
    ecu.step(2)
    low_load = ecu.get_telemetry()

    ecu.set_inputs(rpm=1500, map_kpa=100.0, tps_pct=15.0, coolant_temp_c=85.0)
    ecu.step(2)
    high_load = ecu.get_telemetry()

    assert high_load["actuators"]["fuel_pw_ms"] > low_load["actuators"]["fuel_pw_ms"], \
        "Fuel PW must increase with MAP load at constant RPM"
    assert high_load["actuators"]["spark_advance_deg"] == low_load["actuators"]["spark_advance_deg"], \
        "Spark advance should depend on engine speed and remain constant at identical RPM"

    # 2. Test speed response at constant MAP (60 kPa, 85°C)
    ecu.set_inputs(rpm=1000, map_kpa=60.0, tps_pct=15.0, coolant_temp_c=85.0)
    ecu.step(2)
    low_rpm = ecu.get_telemetry()

    ecu.set_inputs(rpm=3000, map_kpa=60.0, tps_pct=15.0, coolant_temp_c=85.0)
    ecu.step(2)
    high_rpm = ecu.get_telemetry()

    assert high_rpm["actuators"]["spark_advance_deg"] > low_rpm["actuators"]["spark_advance_deg"], \
        "Spark advance must increase with engine RPM"

def test_graceful_shutdown_on_ignition_off(ecu):
    """Verify turning off ignition causes controlled SHUTDOWN -> OFF transition with all outputs disabled."""
    ecu.boot_to_running(rpm=1500)
    assert ecu.get_state() == EcuState.RUNNING

    # Turn key OFF
    ecu.set_inputs(ignition=False, rpm=0)
    ecu.step(1)
    assert ecu.get_state() == EcuState.SHUTDOWN, f"Expected SHUTDOWN, got {ecu.get_state_name()}"
    shutdown_telem = ecu.get_telemetry()
    assert shutdown_telem["actuators"]["fuel_pump"] is False
    assert shutdown_telem["actuators"]["fuel_pw_ms"] == 0.0
    assert shutdown_telem["actuators"]["starter_enable"] is False

    ecu.step(2)
    assert ecu.get_state() == EcuState.OFF, f"Expected OFF after shutdown, got {ecu.get_state_name()}"
    off_telem = ecu.get_telemetry()
    assert off_telem["actuators"]["fuel_pump"] is False
    assert off_telem["actuators"]["fuel_pw_ms"] == 0.0
    assert off_telem["actuators"]["starter_enable"] is False
