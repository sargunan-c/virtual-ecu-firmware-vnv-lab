"""
Automotive Fault Injection Engine (Python Interface).
Defines target channels and fault types matching the C11 Virtual ECU firmware.
"""

from enum import IntEnum

class FaultTarget(IntEnum):
    NONE = 0
    ECT = 1
    TPS = 2
    MAP = 3
    VBATT = 4
    RPM = 5
    CAN = 6

class FaultType(IntEnum):
    NONE = 0
    SHORT_TO_GND = 1
    SHORT_TO_VCC = 2
    OPEN_CIRCUIT = 3
    STUCK_VALUE = 4
    ERRATIC_NOISE = 5
    CAN_TIMEOUT = 6
    TPS_MISMATCH = 7

class FaultInjector:
    """Manages test-time injection of electrical and protocol failures."""

    def __init__(self, adapter):
        self.adapter = adapter

    def inject_sensor_short_gnd(self, target: FaultTarget, duration_ticks: int = 0):
        self.adapter.inject_fault(int(target), int(FaultType.SHORT_TO_GND), 0.0, duration_ticks)

    def inject_sensor_short_vcc(self, target: FaultTarget, duration_ticks: int = 0):
        self.adapter.inject_fault(int(target), int(FaultType.SHORT_TO_VCC), 0.0, duration_ticks)

    def inject_open_circuit(self, target: FaultTarget, duration_ticks: int = 0):
        self.adapter.inject_fault(int(target), int(FaultType.OPEN_CIRCUIT), 0.0, duration_ticks)

    def inject_stuck_value(self, target: FaultTarget, value: float, duration_ticks: int = 0):
        self.adapter.inject_fault(int(target), int(FaultType.STUCK_VALUE), value, duration_ticks)

    def inject_tps_correlation_failure(self, corrupted_tps2_val: float, duration_ticks: int = 0):
        """Violates ASIL-B dual throttle cross-check by forcing TPS2 mismatch."""
        self.adapter.inject_fault(int(FaultTarget.TPS), int(FaultType.TPS_MISMATCH), corrupted_tps2_val, duration_ticks)

    def inject_can_bus_off(self, duration_ticks: int = 0):
        """Simulates CAN gateway transceiver fault / bus off."""
        self.adapter.inject_fault(int(FaultTarget.CAN), int(FaultType.CAN_TIMEOUT), 0.0, duration_ticks)

    def clear_target_fault(self, target: FaultTarget):
        self.adapter.clear_fault(int(target))

    def clear_all(self):
        self.adapter.clear_all_faults()

