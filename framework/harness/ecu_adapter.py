"""
Virtual ECU ctypes Integration Harness.
Bridges Python test scripts directly to C11 Virtual ECU shared library (DLL).
"""

import ctypes
import os
import sys
from pathlib import Path

# C Enum mappings
class EcuState:
    OFF = 0
    INIT = 1
    STANDBY = 2
    RUNNING = 3
    DEGRADED = 4  # Limp-home
    ERROR = 5     # Emergency stop
    SHUTDOWN = 6

    @classmethod
    def to_string(cls, val: int) -> str:
        names = {
            0: "OFF",
            1: "INIT",
            2: "STANDBY",
            3: "RUNNING",
            4: "DEGRADED",
            5: "ERROR",
            6: "SHUTDOWN"
        }
        return names.get(val, f"UNKNOWN({val})")

class DtcCode:
    NONE = 0x0000
    P0115_ECT_CIRCUIT_MALFUNCTION = 0x0115
    P0117_ECT_CIRCUIT_LOW = 0x0117
    P0118_ECT_CIRCUIT_HIGH = 0x0118
    P0217_ENGINE_COOLANT_OVERTEMP = 0x0217
    P0120_TPS_CIRCUIT_MALFUNCTION = 0x0120
    P0121_TPS_RANGE_PERFORMANCE = 0x0121
    P0122_TPS_CIRCUIT_LOW = 0x0122
    P0123_TPS_CIRCUIT_HIGH = 0x0123
    P0105_MAP_CIRCUIT_MALFUNCTION = 0x0105
    P0106_MAP_RANGE_PERFORMANCE = 0x0106
    P0560_SYSTEM_VOLTAGE_MALFUNCTION = 0x0560
    P0562_SYSTEM_VOLTAGE_LOW = 0x0562
    P0563_SYSTEM_VOLTAGE_HIGH = 0x0563
    P0606_ECU_INTERNAL_FAULT = 0x0606
    U0100_LOST_COMM_ECM_GATEWAY = 0xC100

class FanSpeed:
    OFF = 0
    LOW = 1
    HIGH = 2

class MilLamp:
    OFF = 0
    ON = 1
    BLINKING = 2

# C Struct definitions matching ecu_types.h
class SensorInputsC(ctypes.Structure):
    _fields_ = [
        ("coolant_temp_c", ctypes.c_float),
        ("throttle_pos1_pct", ctypes.c_float),
        ("throttle_pos2_pct", ctypes.c_float),
        ("manifold_pressure_kpa", ctypes.c_float),
        ("battery_voltage_v", ctypes.c_float),
        ("engine_rpm", ctypes.c_uint16),
        ("ignition_switch", ctypes.c_bool),
        ("engine_crank_request", ctypes.c_bool),
        ("can_bus_connected", ctypes.c_bool),
    ]

class ActuatorOutputsC(ctypes.Structure):
    _fields_ = [
        ("fuel_injection_pw_ms", ctypes.c_float),
        ("ignition_timing_deg", ctypes.c_float),
        ("cooling_fan_state", ctypes.c_int),
        ("mil_lamp", ctypes.c_int),
        ("throttle_actuator_pct", ctypes.c_float),
        ("fuel_pump_relay", ctypes.c_bool),
        ("starter_relay_enable", ctypes.c_bool),
    ]

class EcuTelemetryC(ctypes.Structure):
    _fields_ = [
        ("cycle_count", ctypes.c_uint32),
        ("uptime_ms", ctypes.c_uint32),
        ("current_state", ctypes.c_int),
        ("previous_state", ctypes.c_int),
        ("raw_inputs", SensorInputsC),
        ("filtered_inputs", SensorInputsC),
        ("actuators", ActuatorOutputsC),
        ("active_dtc_count", ctypes.c_uint8),
        ("active_dtcs", ctypes.c_uint16 * 16),
        ("limp_home_active", ctypes.c_bool),
        ("emergency_stop_active", ctypes.c_bool),
        ("can_timeout_counter", ctypes.c_uint32),
        ("post_passed", ctypes.c_bool),
    ]

class VirtualEcuAdapter:
    """Python interface to the C11 Virtual ECU shared library."""

    def __init__(self, dll_path: str = None):
        if dll_path is None:
            # Locate relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent
            dll_path = str(base_dir / "firmware" / "build" / "virtual_ecu.dll")

        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"Virtual ECU DLL not found at: {dll_path}. Run build.ps1 first.")

        self._lib = ctypes.CDLL(dll_path)
        self._bind_functions()
        self.init()

    def _bind_functions(self):
        self._lib.ecu_init.argtypes = []
        self._lib.ecu_init.restype = None

        self._lib.ecu_reset.argtypes = []
        self._lib.ecu_reset.restype = None

        self._lib.ecu_set_inputs.argtypes = [ctypes.POINTER(SensorInputsC)]
        self._lib.ecu_set_inputs.restype = None

        self._lib.ecu_get_inputs.argtypes = [ctypes.POINTER(SensorInputsC)]
        self._lib.ecu_get_inputs.restype = None

        self._lib.ecu_step.argtypes = [ctypes.c_uint32]
        self._lib.ecu_step.restype = None

        self._lib.ecu_get_telemetry.argtypes = [ctypes.POINTER(EcuTelemetryC)]
        self._lib.ecu_get_telemetry.restype = None

        self._lib.ecu_get_state.argtypes = []
        self._lib.ecu_get_state.restype = ctypes.c_int

        self._lib.ecu_inject_fault.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_float, ctypes.c_uint32]
        self._lib.ecu_inject_fault.restype = None

        self._lib.ecu_clear_fault.argtypes = [ctypes.c_uint8]
        self._lib.ecu_clear_fault.restype = None

        self._lib.ecu_clear_all_faults.argtypes = []
        self._lib.ecu_clear_all_faults.restype = None

        self._lib.ecu_clear_diagnostics.argtypes = []
        self._lib.ecu_clear_diagnostics.restype = None

        self._lib.ecu_is_dtc_active.argtypes = [ctypes.c_uint16]
        self._lib.ecu_is_dtc_active.restype = ctypes.c_bool

        self._lib.ecu_get_active_dtc_count.argtypes = []
        self._lib.ecu_get_active_dtc_count.restype = ctypes.c_uint8

        self._lib.ecu_get_active_dtc_list.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.c_uint8]
        self._lib.ecu_get_active_dtc_list.restype = None

    def init(self):
        self._lib.ecu_init()

    def reset(self):
        self._lib.ecu_reset()

    def set_inputs(self,
                   coolant_temp_c: float = 85.0,
                   tps_pct: float = 20.0,
                   tps2_pct: float = None,
                   map_kpa: float = 101.3,
                   battery_voltage_v: float = 13.8,
                   rpm: int = 800,
                   ignition: bool = True,
                   crank: bool = False,
                   can_connected: bool = True):
        inputs = SensorInputsC()
        inputs.coolant_temp_c = float(coolant_temp_c)
        inputs.throttle_pos1_pct = float(tps_pct)
        # Default TPS2 to ASIL-B correlation: 100 - TPS1
        inputs.throttle_pos2_pct = float(100.0 - tps_pct) if tps2_pct is None else float(tps2_pct)
        inputs.manifold_pressure_kpa = float(map_kpa)
        inputs.battery_voltage_v = float(battery_voltage_v)
        inputs.engine_rpm = int(rpm)
        inputs.ignition_switch = bool(ignition)
        inputs.engine_crank_request = bool(crank)
        inputs.can_bus_connected = bool(can_connected)

        self._lib.ecu_set_inputs(ctypes.byref(inputs))

    def step(self, count: int = 1):
        self._lib.ecu_step(ctypes.c_uint32(count))

    def get_state(self) -> int:
        return self._lib.ecu_get_state()

    def get_state_name(self) -> str:
        return EcuState.to_string(self.get_state())

    def get_telemetry(self) -> dict:
        t = EcuTelemetryC()
        self._lib.ecu_get_telemetry(ctypes.byref(t))

        dtc_list = [t.active_dtcs[i] for i in range(t.active_dtc_count)]
        dtc_hex_list = [f"0x{code:04X}" for code in dtc_list]

        return {
            "cycle_count": t.cycle_count,
            "uptime_ms": t.uptime_ms,
            "state_id": t.current_state,
            "state_name": EcuState.to_string(t.current_state),
            "prev_state_name": EcuState.to_string(t.previous_state),
            "inputs": {
                "coolant_temp_c": round(t.filtered_inputs.coolant_temp_c, 2),
                "tps1_pct": round(t.filtered_inputs.throttle_pos1_pct, 2),
                "tps2_pct": round(t.filtered_inputs.throttle_pos2_pct, 2),
                "map_kpa": round(t.filtered_inputs.manifold_pressure_kpa, 2),
                "battery_voltage_v": round(t.filtered_inputs.battery_voltage_v, 2),
                "rpm": t.filtered_inputs.engine_rpm,
                "ignition": t.filtered_inputs.ignition_switch,
                "can_connected": t.filtered_inputs.can_bus_connected
            },
            "actuators": {
                "fuel_pw_ms": round(t.actuators.fuel_injection_pw_ms, 2),
                "spark_advance_deg": round(t.actuators.ignition_timing_deg, 2),
                "ignition_timing_deg": round(t.actuators.ignition_timing_deg, 2),
                "fan_state": t.actuators.cooling_fan_state,
                "cooling_fan_state": t.actuators.cooling_fan_state,
                "mil_lamp": t.actuators.mil_lamp,
                "throttle_cmd_pct": round(t.actuators.throttle_actuator_pct, 2),
                "fuel_pump": t.actuators.fuel_pump_relay,
                "starter_enable": t.actuators.starter_relay_enable
            },
            "active_dtc_count": t.active_dtc_count,
            "active_dtcs": dtc_hex_list,
            "raw_dtc_codes": dtc_list,
            "limp_home": t.limp_home_active,
            "emergency_stop": t.emergency_stop_active
        }

    def inject_fault(self, target: int, fault_type: int, fixed_value: float = 0.0, duration_ticks: int = 0):
        self._lib.ecu_inject_fault(
            ctypes.c_uint8(target),
            ctypes.c_uint8(fault_type),
            ctypes.c_float(fixed_value),
            ctypes.c_uint32(duration_ticks)
        )

    def clear_fault(self, target: int):
        self._lib.ecu_clear_fault(ctypes.c_uint8(target))

    def clear_all_faults(self):
        self._lib.ecu_clear_all_faults()

    def clear_diagnostics(self):
        self._lib.ecu_clear_diagnostics()

    def is_dtc_active(self, dtc: int) -> bool:
        return bool(self._lib.ecu_is_dtc_active(ctypes.c_uint16(dtc)))

    def boot_to_running(self, rpm: int = 1200):
        """Helper to advance ECU through INIT -> STANDBY -> RUNNING."""
        self.reset()
        self.set_inputs(ignition=True, rpm=rpm)
        # 5 cycles to finish POST (3 ticks) and transition STANDBY -> RUNNING
        self.step(5)
