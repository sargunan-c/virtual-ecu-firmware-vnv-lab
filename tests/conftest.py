"""
Pytest Fixtures for Virtual ECU Test Suite.
"""

import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from framework.harness.ecu_adapter import VirtualEcuAdapter, EcuState, DtcCode, FanSpeed, MilLamp
from simulation.fault_injection.fault_injector import FaultInjector, FaultTarget, FaultType
from simulation.sensors.virtual_sensors import VirtualSensors

@pytest.fixture
def ecu():
    """Provides a fresh Virtual ECU instance initialized and reset."""
    adapter = VirtualEcuAdapter()
    adapter.reset()
    yield adapter
    adapter.clear_all_faults()
    adapter.reset()

@pytest.fixture
def fault_injector(ecu):
    """Provides the fault injector tied to the active ECU instance."""
    return FaultInjector(ecu)

@pytest.fixture
def virtual_sensors():
    """Provides virtual sensor signal generator."""
    return VirtualSensors()

