# Test Plan & Verification Strategy

## Automotive Software Verification & Validation (V&V)

**Project:** Virtual ECU Firmware Verification & Validation Automation Lab  
**Methodology:** Automotive V-Model (Software Unit & Software Integration Testing)  
**Standard:** ISO 26262 Part 6 (Software Level Verification)  

---

### 1. Verification Strategy
Verification is carried out entirely in software using a **Virtual Harness (Host-in-the-Loop)** methodology:
1. **Source Code Level:** C11 firmware compiled with strict compiler flags (`-Wall -Wextra -std=c11 -O2`).
2. **Harness Layer:** Python `ctypes` directly interfaces with the compiled shared library, avoiding IPC or socket latency and guaranteeing cycle-accurate deterministic stepping.
3. **Execution Framework:** `pytest` executes parameterized and targeted test scenarios.
4. **Pass/Fail Criteria:** Zero tolerated assertion failures. Every test case must verify exact state transitions, actuator outputs, and diagnostic bitmask states.

---

### 2. Test Suite Classification

| Suite | Focus Area | Objective | Total Tests |
| :--- | :--- | :--- | :--- |
| **Functional Tests** | State Transitions & Engine Logic | Power states (OFF -> INIT -> STANDBY -> RUNNING -> SHUTDOWN), fuel mapping, and spark timing. | 5 |
| **Sensor Validation** | Calibration & Redundancy | Warm-up fuel enrichment, fan control, and dual TPS correlation. | 3 |
| **Boundary Value Analysis** | Equivalence Partitioning & Limits | Upper/lower limits for ECT (-39°C to 139°C), TPS (0% to 100%), VBATT (8.5V to 16.5V), and MAP (15 kPa to 245 kPa). | 7 |
| **Negative Tests** | Robustness & Error Handling | Negative throttle inputs, electrical collapse, starter lockout during engine run, and illegal state transitions. | 5 |
| **Fault Injection & Recovery** | Safety & Fault Tolerance | Sensor shorts to GND/VCC, open circuit, ASIL-B correlation desync, CAN timeout, debounce confirmation, and self-healing. | 5 |
| **Total Test Cases** | | | **25** |

---

### 3. Traceability & Coverage Matrix
- **Requirements Coverage:** 100% of defined software requirements in `SOFTWARE_REQUIREMENTS_SPECIFICATION.md` have at least one dedicated test case.
- **State Machine Coverage:** 100% of operating states (7/7 states) verified.
- **DTC Coverage:** All 8 primary DTCs validated for qualification and de-qualification.

---

### 4. Regression & Continuous Integration (CI)
All test cases run via a single command:
```bash
python run_all_tests.py
```
Output artifacts are automatically generated in `reports/`:
- `reports/html/dashboard.html` (Interactive visual dashboard)
- `reports/html/pytest_report.html` (Pytest HTML execution trace)
- `reports/json/test_results.json` (Machine-readable CI/CD artifact)
- `reports/csv/test_results.csv` (Traceability summary sheet)
