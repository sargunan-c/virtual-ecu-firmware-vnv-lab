# Virtual ECU Firmware Verification & Validation (V&V) Automation Lab

[![Firmware Language](https://img.shields.io/badge/Firmware-C11-00599C.svg)](firmware/)
[![Automation Framework](https://img.shields.io/badge/Automation-Python_3.14-3776AB.svg)](framework/)
[![Test Runner](https://img.shields.io/badge/Testing-Pytest_9.2-0A9EDC.svg)](tests/)
[![Safety Standard](https://img.shields.io/badge/Safety_Standard-ISO_26262_ASIL--B_Concept-brightgreen.svg)](docs/SOFTWARE_REQUIREMENTS_SPECIFICATION.md)
[![Diagnostics](https://img.shields.io/badge/Diagnostics-ISO_14229_UDS-orange.svg)](docs/ARCHITECTURE_DESIGN_DOCUMENT.md)
[![Test Status](https://img.shields.io/badge/Test_Results-25%2F25_PASSED_(100%25)-success.svg)](reports/html/dashboard.html)

---

## Executive Summary

The **Virtual ECU Firmware Verification & Validation (V&V) Automation Lab** is a professional, software-in-the-loop (SIL) test automation ecosystem modeled after Tier-1 automotive embedded software engineering workflows. It provides a host-simulated **Powertrain & Thermal Control Unit (PTCU)** developed in **C11**, coupled to a deterministic **Python / Pytest automation harness** via native C-ABI bindings (`ctypes`).

The project demonstrates end-to-end verification and validation of automotive ECU firmware—encompassing deterministic finite state machine (FSM) control, AUTOSAR DEM / ISO 14229 UDS diagnostic debounce algorithms, ISO 26262 ASIL-B dual-channel sensor plausibility interlocks, non-intrusive runtime fault injection, boundary value analysis (BVT), negative testing, and automated HTML5 dashboard reporting.

> **Note on Scope:** This is a 100% software-only simulation environment. No physical hardware boards, microcontrollers, or external CAN transceivers are required. All ECU operations, physics, and sensor lines are simulated virtually.

---

## System Architecture

```
+---------------------------------------------------------------------------------+
|                       AUTOMATED TEST SUITE (PYTEST 9.2)                         |
|  [Functional Tests]   [Boundary Tests]   [Negative Tests]   [Fault Recovery]    |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
|                       AUTOMATION & HARNESS LAYER (PYTHON)                       |
|  VirtualEcuAdapter (ctypes)  <--->  FaultInjector  <--->  VirtualSensors        |
|  TelemetryLogger (CSV/JSON)  <--->  ReportGenerator (HTML Dashboard)            |
+---------------------------------------------------------------------------------+
                                       |  (Native C-ABI Shared Library Calls)
                                       v
+---------------------------------------------------------------------------------+
|                     VIRTUAL ECU FIRMWARE ENGINE (C11 DLL)                       |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | Fault Injection Hook (Signal interception & physical manipulation)        |  |
|  +---------------------------------------------------------------------------+  |
|                                      |                                          |
|                                      v                                          |
|  +---------------------+   +---------------------+   +---------------------+    |
|  | Sensor Acquisition  |-->|  Diagnostic Manager |-->| Finite State Machine|    |
|  | - Range validation  |   |  - Debounce counter |   | - OFF, INIT, STANDBY|    |
|  | - ASIL-B Dual TPS   |   |  - UDS ISO 14229    |   | - RUNNING, DEGRADED |    |
|  | - Fallback maps     |   |  - DTC confirm/heal |   | - ERROR, SHUTDOWN   |    |
|  +---------------------+   +---------------------+   +---------------------+    |
|                                                                 |               |
|                                                                 v               |
|                                                      +---------------------+    |
|                                                      | Actuator Controller |    |
|                                                      | - Fuel Injection PW |    |
|                                                      | - Spark Advance     |    |
|                                                      | - Cooling Fan PWM   |    |
|                                                      | - Check Engine MIL  |    |
|                                                      +---------------------+    |
+---------------------------------------------------------------------------------+
```

---

## Core Engineering Features

### 1. Deterministic ECU Operating State Machine (FSM)
Orchestrates vehicle operational modes across 7 strict states with 10 ms cycle rate:
- **`ECU_STATE_OFF`:** Zero actuator activity, waiting for ignition switch.
- **`ECU_STATE_INIT`:** 30 ms Power-On Self Test (POST) checking system integrity.
- **`ECU_STATE_STANDBY`:** Ignition ON, fuel pump primed, starter enabled, waiting for crank.
- **`ECU_STATE_RUNNING`:** Closed-loop engine speed and throttle plate regulation.
- **`ECU_STATE_DEGRADED` (Limp-Home):** Safe fallback maps active, throttle capped at 25%, MIL lit.
- **`ECU_STATE_ERROR` (Emergency Stop):** Immediate fuel cut-off, spark advance killed, high-speed cooling fan active, MIL blinking.
- **`ECU_STATE_SHUTDOWN`:** Diagnostic non-volatile record flushing before power-down.

### 2. ISO 14229 / AUTOSAR DEM Diagnostic Manager
- Asymmetric debounce timing:
  - **Qualification:** 5 consecutive failure cycles (50 ms) confirms DTC and illuminates MIL.
  - **Self-Healing:** 10 consecutive clean cycles (100 ms) heals confirmed DTC and extinguishes MIL.
- Monitored DTCs:
  - `P0117` / `P0118`: Engine Coolant Temperature Circuit Low / High
  - `P0217`: Engine Coolant Over-temperature (> 118°C Critical Overheat)
  - `P0121`: Dual Throttle Position Sensor Correlation Mismatch (ASIL-B)
  - `P0122` / `P0123`: Throttle Circuit Low / High
  - `P0106`: Manifold Absolute Pressure Range Fault
  - `P0562` / `P0563`: Battery Undervoltage (< 8.5V) / Overvoltage (> 16.5V)
  - `U0100`: Lost CAN Communication with Vehicle Gateway

### 3. ISO 26262 ASIL-B Electronic Throttle Plausibility
Complementary dual-potentiometer verification:
$$\left| \text{TPS}_1 + \text{TPS}_2 - 100\% \right| \le 7.0\%$$
Any discrepancy exceeding 7% triggers `DTC_P0121` and commands an immediate transition to `ECU_STATE_ERROR` (Emergency Stop) within 50 ms.

### 4. Non-Intrusive Runtime Fault Injection Engine
Supports software-directed electrical and protocol failure simulation:
- Signal short to Ground (`0V` / `-45°C` / `-5%`)
- Signal short to Power (`VCC` / `150°C` / `115%`)
- Sensor open circuit / floating pull-down
- Sensor stuck-at value
- CAN bus-off / heartbeat timeout

---

## Repository Structure

```
virtual_ecu_vnv_lab/
├── firmware/                        # C11 Virtual ECU Source Code
│   ├── include/                     # Public and subsystem header files
│   │   ├── ecu_types.h              # Data structures, enums, DTC bitmasks
│   │   ├── ecu_firmware.h           # Top-level API & DLL export definitions
│   │   ├── ecu_state_machine.h      # FSM definitions
│   │   ├── ecu_diagnostics.h        # OBD-II / ISO 14229 DEM header
│   │   ├── ecu_sensors.h            # Sensor processing & bounds definitions
│   │   ├── ecu_actuators.h          # Actuator output calculations
│   │   └── ecu_fault_injection.h    # Fault injection interceptor header
│   ├── src/                         # C11 Implementation files
│   │   ├── ecu_firmware.c           # Master cycle coordinator
│   │   ├── ecu_state_machine.c      # FSM implementation
│   │   ├── ecu_diagnostics.c        # DTC debounce & MIL manager
│   │   ├── ecu_sensors.c            # Boundary validation & dual TPS correlation
│   │   ├── ecu_actuators.c          # Injection PW, timing & fan control
│   │   ├── ecu_fault_injection.c    # Signal corruption hooks
│   │   └── main.c                   # Standalone CLI binary runner
│   └── build/                       # Compiled artifacts (virtual_ecu.dll, virtual_ecu.exe)
├── simulation/                      # Simulation Modules
│   ├── sensors/virtual_sensors.py   # Physical sensor models & thermal dynamics
│   └── fault_injection/fault_injector.py # Python fault injection interface
├── framework/                       # Test Harness & Reporting Infrastructure
│   ├── harness/ecu_adapter.py       # Ctypes C-ABI bridge to virtual_ecu.dll
│   ├── telemetry/logger.py          # High-rate cycle snapshot logger
│   └── reporting/report_generator.py # Standalone HTML5 dashboard generator
├── tests/                           # Pytest Test Automation Suites
│   ├── conftest.py                  # Pytest fixtures and harness setup
│   ├── functional/                  # Normal operation & state transitions
│   ├── boundary/                    # Boundary Value Analysis (BVT)
│   ├── negative/                    # Error handling & illegal state transitions
│   └── fault_recovery/              # FDIR & self-healing verification
├── test_data/                       # Calibration and Scenario Input Files
│   ├── scenarios.json               # Pre-configured test scenario vectors
│   └── sensor_profiles.csv          # Driving cycle test profiles
├── reports/                         # Generated Test Verification Artifacts
│   ├── html/                        # Interactive dashboard & Pytest reports
│   │   ├── dashboard.html           # Interactive visual dashboard
│   │   └── pytest_report.html       # Pytest HTML execution trace
│   ├── json/                        # Structured machine-readable results
│   └── csv/                         # Requirements traceability test sheets
├── docs/                            # Professional Engineering Documentation
│   ├── SOFTWARE_REQUIREMENTS_SPECIFICATION.md
│   ├── ARCHITECTURE_DESIGN_DOCUMENT.md
│   ├── TEST_PLAN_AND_STRATEGY.md
│   ├── TEST_CASE_SPECIFICATION.md
│   ├── TECHNICAL_CHALLENGES_AND_SOLUTIONS.md
│   └── PORTFOLIO_DEMO_GUIDE.md
├── build.ps1                        # PowerShell one-click compiler
├── Makefile                         # Standard Make build script
├── run_all_tests.py                 # Master automated test execution runner
├── run_demo_simulation.py           # Mission driving cycle telemetry generator
└── README.md                        # Master project documentation
```

---

## Quick Start & Execution Guide

### Prerequisites
- GCC / MinGW C Compiler (with C11 standard support)
- Python 3.10+
- Pytest and Pytest-HTML (`pip install pytest pytest-html`)

### 1. Build the Firmware
Compile both the shared library (`virtual_ecu.dll`) and standalone executable (`virtual_ecu.exe`):

**Via PowerShell:**
```powershell
./build.ps1
```

**Via Make:**
```bash
make
```

### 2. Run the Standalone Virtual ECU CLI
Execute the C firmware binary directly:
```powershell
./firmware/build/virtual_ecu.exe
```

### 3. Run the Automated Test Suite (Pytest)
Run all 25 test cases across Boundary, Negative, Functional, and Fault Recovery suites:
```powershell
python run_all_tests.py
```

### 4. Run Mission Simulation & Export Telemetry
Simulate a complete driving cycle with live fault injection and recovery:
```powershell
python run_demo_simulation.py
```

---

## Test Execution Results

```
======================================================================
  AUTOMOTIVE VIRTUAL ECU V&V AUTOMATION LAB - TEST EXECUTION RUNNER
======================================================================
[Runner] Executing test suite via pytest...
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\...\virtual_ecu_vnv_lab
plugins: anyio-4.15.1, html-4.2.0, metadata-3.1.1
collected 25 items

tests/boundary/test_boundary_values.py::test_ect_lower_valid_boundary PASSED [  4%]
tests/boundary/test_boundary_values.py::test_ect_below_lower_boundary_triggers_fault PASSED [  8%]
tests/boundary/test_boundary_values.py::test_ect_upper_valid_boundary PASSED [ 12%]
tests/boundary/test_boundary_values.py::test_ect_above_upper_boundary_triggers_circuit_high PASSED [ 16%]
tests/boundary/test_boundary_values.py::test_ect_overheat_critical_boundary PASSED [ 20%]
tests/boundary/test_boundary_values.py::test_battery_voltage_boundaries PASSED [ 24%]
tests/boundary/test_boundary_values.py::test_throttle_limits_and_clamping PASSED [ 28%]
tests/fault_recovery/test_fault_detection_recovery.py::test_ect_short_gnd_fault_qualification_and_recovery PASSED [ 32%]
tests/fault_recovery/test_fault_detection_recovery.py::test_asil_b_dual_tps_mismatch_emergency_stop PASSED [ 36%]
tests/fault_recovery/test_fault_detection_recovery.py::test_critical_thermal_overheat_emergency_stop PASSED [ 40%]
tests/fault_recovery/test_fault_detection_recovery.py::test_can_communication_timeout_and_recovery PASSED [ 44%]
tests/fault_recovery/test_fault_detection_recovery.py::test_map_sensor_fault_injection_and_fallback PASSED [ 48%]
tests/functional/test_normal_operation.py::test_ecu_initial_state_off PASSED [ 52%]
tests/functional/test_normal_operation.py::test_ecu_power_on_and_post_sequence PASSED [ 56%]
tests/functional/test_normal_operation.py::test_engine_cranking_to_running PASSED [ 60%]
tests/functional/test_fuel_injection_and_spark_advance_dynamics PASSED [ 64%]
tests/functional/test_graceful_shutdown_on_ignition_off PASSED [ 68%]
tests/functional/test_sensor_validation.py::test_cold_start_fuel_enrichment PASSED [ 72%]
tests/functional/test_sensor_validation.py::test_cooling_fan_activation_thresholds PASSED [ 76%]
tests/functional/test_sensor_validation.py::test_dual_throttle_correlation_valid PASSED [ 80%]
tests/negative/test_negative_scenarios.py::test_negative_throttle_input_triggers_circuit_low PASSED [ 84%]
tests/negative/test_negative_scenarios.py::test_over_range_throttle_input_triggers_circuit_high PASSED [ 88%]
tests/negative/test_negative_scenarios.py::test_starter_lockout_while_engine_running PASSED [ 92%]
tests/negative/test_negative_scenarios.py::test_zero_voltage_electrical_collapse PASSED [ 96%]
tests/negative/test_negative_scenarios.py::test_invalid_state_transition_no_crank_without_ignition PASSED [100%]

============================= 25 passed in 0.38s ==============================
[Report] Generated JSON results at: reports/json/test_results.json
[Report] Generated CSV results at: reports/csv/test_results.csv
[Report] Generated Interactive Dashboard at: reports/html/dashboard.html
======================================================================
  EXECUTION SUMMARY: 25/25 PASSED (100.0%) in 4.17s
======================================================================
```

---

## Interactive HTML5 Test Dashboard Preview

The test automation runner automatically compiles an interactive, self-contained dashboard located at:
`reports/html/dashboard.html`

### Key Visual Components:
- **KPI Summary Cards:** Total Tests (25), Passed (25), Failed (0), Pass Rate (100%), Total Execution Time.
- **Category Coverage:** Visual breakdown across Boundary, Negative, Functional, Sensor, and Fault Recovery tests.
- **State Machine Verification Grid:** All 7 operating states validated against unauthorized state transitions.
- **Requirements Traceability Table:** Interactive table mapping each test to its specific Software Requirement ID (`REQ-BVT`, `REQ-FDIR`, `REQ-FSM`).

---

## Requirements Traceability Summary

| Category | Tests | SRS Traceability | Pass Rate |
| :--- | :---: | :--- | :---: |
| **Boundary Value Analysis (BVT)** | 7 | `REQ-BVT-001` through `REQ-BVT-007` | **100%** |
| **Fault Detection & Recovery (FDIR)** | 5 | `REQ-FDIR-001` through `REQ-FDIR-005` | **100%** |
| **Functional & State Transitions** | 5 | `REQ-FSM-001` - `004`, `REQ-ACT-001` | **100%** |
| **Sensor Validation & Redundancy** | 3 | `REQ-SENS-001`, `REQ-SENS-002`, `REQ-ACT-002` | **100%** |
| **Negative & Robustness Testing** | 5 | `REQ-NEG-001` through `REQ-NEG-005` | **100%** |
| **Total** | **25** | **100% Requirements Coverage** | **100%** |

---

## Industry Relevance & Automotive Skills Demonstrated

This project demonstrates core competencies sought by automotive OEMs and Tier-1 suppliers in India (Tata Motors, Mahindra, Bosch India, Continental, KPIT, Tata Elxsi, Ather Energy):

- **Automotive Embedded C (C11):** MISRA-C compliant patterns, zero heap allocation, deterministic timing, struct packing.
- **ECU Concepts & State Machines:** Multi-state power control, cold-start warmup enrichment, speed-density fuel calculation, starter interlocks.
- **Automotive Diagnostics (ISO 14229 / AUTOSAR DEM):** DTC qualification/healing debounce algorithms, MIL lamp management.
- **Functional Safety (ISO 26262 ASIL-B Concept):** Dual-channel throttle plausibility, fail-safe degradation, emergency stop fuel cut-off.
- **Verification & Validation (V&V):** Boundary value testing, negative testing, automated regression test authoring using Python and Pytest.
- **Software Test Tooling:** Native C-ABI bindings via `ctypes`, automated HTML/JSON/CSV reporting, continuous integration readiness.

---

## Disclaimer
*This software is an engineering verification and validation simulation laboratory developed strictly for educational, technical demonstration, and career portfolio purposes. It does not claim OEM vehicle certification or physical road validation.*

