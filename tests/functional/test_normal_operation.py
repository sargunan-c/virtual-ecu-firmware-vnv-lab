"""
Test Suite: Normal ECU Operation & Operating State Transitions
Validates power states, startup POST, standby, running, and controlled shutdown.
"""

from framework.harness.ecu_adapter import EcuState, FanSpeed, MilLamp

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
    """Verify Ignition ON triggers INIT -> POST -> STANDBY."""
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
    """Verify cranking signal transitions ECU from STANDBY to RUNNING when RPM exceeds threshold."""
    ecu.set_inputs(ignition=True, rpm=0)
    ecu.step(4)  # Arrive in STANDBY
    assert ecu.get_state() == EcuState.STANDBY

    # Crank engine up to 500 RPM (above cranking threshold of 450 RPM)
    ecu.set_inputs(ignition=True, rpm=500, crank=True)
    ecu.step(1)
    assert ecu.get_state() == EcuState.RUNNING, f"Expected RUNNING after crank, got {ecu.get_state_name()}"

    telem = ecu.get_telemetry()
    assert telem["actuators"]["starter_enable"] is False, "Starter must disengage once engine runs"
    assert telem["actuators"]["fuel_pw_ms"] > 0.0, "Fuel injection pulse width must be positive"

def test_fuel_injection_and_spark_advance_dynamics(ecu):
    """Verify fuel pulse width and spark advance scale correctly with RPM and engine load."""
    ecu.boot_to_running(rpm=1000)
    ecu.set_inputs(rpm=1000, map_kpa=50.0, tps_pct=15.0, coolant_temp_c=85.0)
    ecu.step(2)
    idle_telem = ecu.get_telemetry()

    # Increase RPM to 3500 and MAP to 120 kPa (high load acceleration)
    ecu.set_inputs(rpm=3500, map_kpa=120.0, tps_pct=60.0, coolant_temp_c=85.0)
    ecu.step(2)
    high_load_telem = ecu.get_telemetry()

    assert high_load_telem["actuators"]["fuel_pw_ms"] > idle_telem["actuators"]["fuel_pw_ms"], \
        "Fuel PW should increase under load and RPM"
    assert high_load_telem["actuators"]["spark_advance_deg"] > idle_telem["actuators"]["spark_advance_deg"], \
        "Spark advance must increase with engine speed"

def test_graceful_shutdown_on_ignition_off(ecu):
    """Verify turning off ignition causes controlled SHUTDOWN -> OFF transition."""
    ecu.boot_to_running(rpm=1500)
    assert ecu.get_state() == EcuState.RUNNING

    # Turn key OFF
    ecu.set_inputs(ignition=False, rpm=0)
    ecu.step(1)
    assert ecu.get_state() == EcuState.SHUTDOWN, f"Expected SHUTDOWN, got {ecu.get_state_name()}"

    ecu.step(2)
    assert ecu.get_state() == EcuState.OFF, f"Expected OFF after shutdown, got {ecu.get_state_name()}"
    telem = ecu.get_telemetry()
    assert telem["actuators"]["fuel_pump"] is False
