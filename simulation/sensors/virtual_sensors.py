"""
Virtual Automotive Sensor Models.
Simulates physical dynamics, thermal inertia, dual-channel potentiometers,
and engine operational curves.
"""

import math
import random
from dataclasses import dataclass

@dataclass
class SensorProfile:
    coolant_temp_c: float = 85.0
    throttle_pct: float = 20.0
    manifold_pressure_kpa: float = 101.3
    battery_voltage_v: float = 13.8
    engine_rpm: int = 800
    ignition_switch: bool = True
    crank_request: bool = False
    can_alive: bool = True

class VirtualSensors:
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.state = SensorProfile()

    def set_nominal_running(self, rpm: int = 1500, throttle_pct: float = 25.0) -> SensorProfile:
        """Configures clean nominal operating point for running engine."""
        self.state.ignition_switch = True
        self.state.crank_request = False
        self.state.can_alive = True
        self.state.engine_rpm = rpm
        self.state.throttle_pct = throttle_pct
        self.state.coolant_temp_c = 90.0
        # Speed-density approx: MAP increases with throttle
        self.state.manifold_pressure_kpa = 30.0 + (throttle_pct * 0.7)
        self.state.battery_voltage_v = 14.1
        return self.state

    def set_cold_start(self, ambient_temp_c: float = -10.0) -> SensorProfile:
        """Configures cold engine ready for ignition and cranking."""
        self.state.ignition_switch = True
        self.state.crank_request = True
        self.state.can_alive = True
        self.state.engine_rpm = 250  # cranking speed
        self.state.throttle_pct = 0.0
        self.state.coolant_temp_c = ambient_temp_c
        self.state.manifold_pressure_kpa = 101.3  # atmospheric
        self.state.battery_voltage_v = 10.2  # cranking voltage dip
        return self.state

    def set_overheat_scenario(self, temp_c: float = 120.0) -> SensorProfile:
        """Simulates engine cooling failure."""
        self.state.coolant_temp_c = temp_c
        return self.state

    def set_dual_throttle(self, commanded_pct: float, mismatch_offset: float = 0.0) -> tuple[float, float]:
        """
        Generates ASIL-B dual throttle potentiometer signals.
        TPS1: 0% to 100%
        TPS2: (100% - TPS1) + mismatch_offset
        """
        tps1 = max(0.0, min(100.0, commanded_pct))
        tps2 = max(0.0, min(100.0, (100.0 - tps1) + mismatch_offset))
        return tps1, tps2
