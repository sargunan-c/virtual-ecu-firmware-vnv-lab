"""
Demonstration Mission Simulation Runner.
Executes an end-to-end mission cycle demonstrating:
1. Power-on POST & Start
2. Nominal High-Speed Cruise
3. ECT Sensor Short Injection & Limp-Home Entry
4. Fault Healing & Recovery to Nominal
5. Controlled Ignition-Off Shutdown
Outputs full cycle-by-cycle telemetry logs to CSV and JSON.
"""

import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from framework.harness.ecu_adapter import VirtualEcuAdapter, EcuState, FanSpeed, MilLamp
from simulation.fault_injection.fault_injector import FaultInjector, FaultTarget
from framework.telemetry.logger import TelemetryLogger

def run_mission():
    print("=" * 65)
    print("  VIRTUAL ECU MISSION SIMULATION & CYCLE-BY-CYCLE TELEMETRY")
    print("=" * 65)

    ecu = VirtualEcuAdapter()
    fault_injector = FaultInjector(ecu)
    logger = TelemetryLogger(log_name="mission_telemetry")

    # Phase 1: Key-OFF (100ms)
    print(">>> Phase 1: Key-OFF state...")
    ecu.set_inputs(ignition=False, rpm=0)
    for _ in range(10):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())

    # Phase 2: Key-ON & POST (200ms)
    print(">>> Phase 2: Key-ON -> POST -> STANDBY...")
    ecu.set_inputs(ignition=True, rpm=0, coolant_temp_c=25.0)
    for _ in range(20):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())

    # Phase 3: Engine Crank & Ramp-up to Idle (300ms)
    print(">>> Phase 3: Engine Cranking -> RUNNING at 850 RPM...")
    ecu.set_inputs(ignition=True, crank=True, rpm=500, coolant_temp_c=30.0)
    for _ in range(10):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())

    ecu.set_inputs(ignition=True, crank=False, rpm=850, map_kpa=40.0, tps_pct=8.0, coolant_temp_c=45.0)
    for _ in range(20):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())

    # Phase 4: Nominal Acceleration & Warmup (500ms)
    print(">>> Phase 4: Acceleration to 2800 RPM Cruise, Temp 90°C...")
    ecu.set_inputs(ignition=True, rpm=2800, map_kpa=85.0, tps_pct=35.0, coolant_temp_c=90.0)
    for _ in range(50):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())

    # Phase 5: Inject Fault - ECT Short to GND (-45°C) -> Limp Home (300ms)
    print(">>> Phase 5: Fault Injection - ECT Short to GND (-45°C)...")
    fault_injector.inject_sensor_short_gnd(FaultTarget.ECT)
    for _ in range(30):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())
    telem = ecu.get_telemetry()
    print(f"    State during fault: {telem['state_name']} | MIL: {telem['actuators']['mil_lamp']} | DTCs: {telem['active_dtcs']}")

    # Phase 6: Clear Fault & Recover to RUNNING (400ms)
    print(">>> Phase 6: Healing - Clear Fault & Return to RUNNING...")
    fault_injector.clear_target_fault(FaultTarget.ECT)
    for _ in range(40):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())
    telem = ecu.get_telemetry()
    print(f"    State after recovery: {telem['state_name']} | MIL: {telem['actuators']['mil_lamp']} | Active DTCs: {telem['active_dtc_count']}")

    # Phase 7: Ignition OFF & Controlled Shutdown (200ms)
    print(">>> Phase 7: Key-OFF Graceful Shutdown...")
    ecu.set_inputs(ignition=False, rpm=0)
    for _ in range(20):
        ecu.step(1)
        logger.log_cycle(ecu.get_telemetry())

    # Export Telemetry Logs
    csv_file = logger.export_csv()
    json_file = logger.export_json()

    print("=" * 65)
    print(f"[Done] Total cycles simulated: {len(logger.records)} (approx {len(logger.records)*10} ms)")
    print(f"[Done] Telemetry CSV: {csv_file}")
    print(f"[Done] Telemetry JSON: {json_file}")
    print("=" * 65)

if __name__ == "__main__":
    run_mission()
