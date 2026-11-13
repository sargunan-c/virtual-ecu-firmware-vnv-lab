# Software Requirements Specification (SRS)

## Virtual Powertrain & Thermal Control Unit (PTCU) Firmware

**Document ID:** SRS-VECU-2026-V1.0  
**Standard Compliance:** ISO 26262 ASIL-B Inspired, ISO 14229-1 (UDS Diagnostics)  
**Target Environment:** Host-Simulated C11 Virtual ECU  

---

### 1. Purpose & Scope
This specification defines the functional, diagnostic, safety, and boundary requirements for the Virtual Powertrain & Thermal Control Unit (PTCU) firmware. All requirements are verified via automated Python/Pytest test suites with hardware-in-the-loop (HIL) simulation fidelity in software.

---

### 2. Functional Requirements

| Req ID | Module | Description | Verification Method |
| :--- | :--- | :--- | :--- |
| **REQ-FSM-001** | State Machine | The ECU shall remain in `ECU_STATE_OFF` with zero actuator activity when the ignition switch is false. | Automated Pytest |
| **REQ-FSM-002** | State Machine | When ignition switch transitions to true, the ECU shall transition to `ECU_STATE_INIT`, complete a 3-cycle POST, and transition to `ECU_STATE_STANDBY`. | Automated Pytest |
| **REQ-FSM-003** | State Machine | In `STANDBY`, when engine RPM exceeds 450 RPM, the ECU shall transition to `ECU_STATE_RUNNING`. | Automated Pytest |
| **REQ-FSM-004** | State Machine | When ignition switch transitions to false from any active state, the ECU shall transition to `ECU_STATE_SHUTDOWN` and then `ECU_STATE_OFF`. | Automated Pytest |
| **REQ-ACT-001** | Actuators | In `RUNNING`, fuel pulse width (ms) and spark advance (deg) shall dynamically scale with MAP and RPM. | Automated Pytest |
| **REQ-ACT-002** | Actuators | Cooling fan shall activate at `LOW_SPEED` when coolant temp ≥ 95°C and `HIGH_SPEED` when temp ≥ 105°C. | Automated Pytest |
| **REQ-SENS-001** | Sensors | When coolant temperature is below 60°C, the ECU shall apply cold start fuel enrichment. | Automated Pytest |
| **REQ-SENS-002** | Sensors | Dual throttle signals (TPS1, TPS2) shall be cross-verified according to complementary law: `TPS1 + TPS2 = 100% ± 7%`. | Automated Pytest |

---

### 3. Boundary & Physical Limits Requirements

| Req ID | Signal | Valid Range | Failure Threshold | Action |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-BVT-001** | Coolant Temp (ECT) | -39.0°C to 139.0°C | ECT ≥ -39.0°C | No fault qualified |
| **REQ-BVT-002** | Coolant Temp (ECT) | -39.0°C to 139.0°C | ECT < -39.0°C | Qualify DTC P0117, Fallback to 85°C |
| **REQ-BVT-003** | Coolant Temp (ECT) | -39.0°C to 139.0°C | ECT ≤ 139.0°C | No fault qualified |
| **REQ-BVT-004** | Coolant Temp (ECT) | -39.0°C to 139.0°C | ECT > 139.0°C | Qualify DTC P0118, Fallback to 85°C |
| **REQ-BVT-005** | Coolant Temp (ECT) | < 118.0°C | ECT ≥ 118.0°C | Qualify DTC P0217, Emergency Stop |
| **REQ-BVT-006** | Battery Voltage | 8.5V to 16.5V | V < 8.5V or V > 16.5V | Qualify P0562 (Low) or P0563 (High) |
| **REQ-BVT-007** | Throttle Command | 0.0% to 100.0% | Outside [0, 100] | Clamped within [0.0, 100.0]% |

---

### 4. Safety & Fault Detection, Isolation, and Recovery (FDIR)

| Req ID | Fault Mode | Debounce Cycles | Fail-Safe State | Recovery Condition |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-FDIR-001** | ECT Short to GND | 5 cycles (50 ms) | `ECU_STATE_DEGRADED` (Limp-Home), MIL ON, Default 85°C | 10 consecutive clean cycles |
| **REQ-FDIR-002** | ASIL-B Dual TPS Mismatch | 5 cycles (50 ms) | `ECU_STATE_ERROR` (Emergency Stop), Fuel Cutoff, Spark Kill, MIL Blinking | Non-recovering without power cycle |
| **REQ-FDIR-003** | Thermal Overheat (>118°C) | 5 cycles (50 ms) | `ECU_STATE_ERROR` (Emergency Stop), Fan High Speed, Fuel Cutoff | Power cycle / cooldown |
| **REQ-FDIR-004** | CAN Gateway Loss | 5 cycles (50 ms) | `ECU_STATE_DEGRADED` (Limp-Home), Throttle capped at 25% | CAN heartbeat restored |
| **REQ-FDIR-005** | MAP Out of Range | 5 cycles (50 ms) | `ECU_STATE_DEGRADED`, Default MAP 101.3 kPa | 10 clean cycles |

---

### 5. Negative Scenarios & Interlocks

| Req ID | Condition | Expected System Behavior |
| :--- | :--- | :--- |
| **REQ-NEG-001** | TPS < 0.0% (Short to GND) | Qualify DTC P0122, Clamp actuator command to 0.0% |
| **REQ-NEG-002** | TPS > 100.0% (Short to VCC) | Qualify DTC P0123, Clamp actuator command to 100.0% |
| **REQ-NEG-003** | Starter crank while RPM > 400 | Starter relay lockout (`starter_enable = false`) |
| **REQ-NEG-004** | Battery Voltage drops to 0.0V | Immediate low-voltage fault qualification |
| **REQ-NEG-005** | Crank command without Ignition | Inhibit starter and fuel pump; remain in OFF |

