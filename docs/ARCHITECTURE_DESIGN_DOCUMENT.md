# Architecture Design Document (ADD)

## Virtual ECU Firmware Verification & Validation Automation Lab

**Document ID:** ADD-VECU-2026-V1.0  
**Target:** Host-in-the-Loop Simulation Architecture  

---

### 1. System High-Level Architecture

The Virtual ECU test platform is structured as a closed-loop automotive simulation environment with a strict separation between firmware logic, fault injection, sensor physics, test harness, and test reporting.

```
+---------------------------------------------------------------------------------+
|                         AUTOMATED TEST SUITE (PYTEST)                           |
|  [Functional Tests]   [Boundary Tests]   [Negative Tests]   [Fault Recovery]    |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
|                       AUTOMATION & HARNESS LAYER (PYTHON)                       |
|  VirtualEcuAdapter (ctypes)  <--->  FaultInjector  <--->  VirtualSensors        |
|  TelemetryLogger (CSV/JSON)  <--->  ReportGenerator (HTML Dashboard)            |
+---------------------------------------------------------------------------------+
                                       |  (C ABI / DLL Function Calls)
                                       v
+---------------------------------------------------------------------------------+
|                     VIRTUAL ECU FIRMWARE ENGINE (C11 DLL)                       |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | Fault Injection Hook (Signal interception & manipulation)                |  |
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

### 2. Finite State Machine (FSM) Transitions

```
               +--------------------------------------+
               |             ECU_STATE_OFF            |
               +--------------------------------------+
                                  | Ignition ON
                                  v
               +--------------------------------------+
               |            ECU_STATE_INIT            |
               |       (Power-On Self Test 30ms)      |
               +--------------------------------------+
                                  | POST OK
                                  v
               +--------------------------------------+
         +---->|          ECU_STATE_STANDBY           |<----+
         |     +--------------------------------------+     |
         |         | Crank & RPM > 450      | Critical DTC  |
         |         v                        v               |
         |     +------------------+     +-------------+     |
         |     |    ECU_STATE_    |     | ECU_STATE_  |     |
         |     |     RUNNING      |     |    ERROR    |     |
         |     +------------------+     | (E-Stop)    |     |
         |       | Degraded  ^ Recover  +-------------+     |
         |       v Fault     | Clean           |            |
         |     +------------------+            |            |
         |     |    ECU_STATE_    |            |            |
         |     |     DEGRADED     |            |            |
         |     |   (Limp-Home)    |            |            |
         |     +------------------+            |            |
         | Engine Stall |                      |            |
         +--------------+                      |            |
                                               | Key OFF    |
                                               v            |
               +--------------------------------------+     |
               |          ECU_STATE_SHUTDOWN          |-----+
               +--------------------------------------+
```

---

### 3. Diagnostic Manager & ISO 14229 / AUTOSAR DEM Logic

Each Diagnostic Trouble Code (DTC) adheres to automotive debounce standards:
1. **Qualification Debounce:** `DTC_DEBOUNCE_CONFIRM_CYCLES` = 5 consecutive failing cycles (50 ms).
   - Bit 0: `TestFailed`
   - Bit 2: `PendingDTC`
   - Bit 3: `ConfirmedDTC`
   - Bit 7: `WarningIndicatorRequested` (MIL)
2. **Self-Healing Debounce:** `DTC_DEBOUNCE_HEAL_CYCLES` = 10 consecutive clean cycles (100 ms).
   - De-qualifies confirmed DTCs and turns off the Malfunction Indicator Lamp.
3. **Critical DTCs:** Immediately trigger `ECU_STATE_ERROR` (Emergency Stop):
   - `DTC_P0217`: Engine Coolant Over-temperature (> 118°C)
   - `DTC_P0121`: ASIL-B Dual Throttle Position Sensor Mismatch
   - `DTC_P0563`: Vehicle System Overvoltage (> 16.5V)
   - `DTC_P0606`: Internal Processor / RAM Watchdog Fault
4. **Degraded DTCs:** Trigger `ECU_STATE_DEGRADED` (Limp-Home):
   - `DTC_P0117` / `DTC_P0118`: ECT Sensor Circuit Low / High
   - `DTC_P0106`: Manifold Absolute Pressure Sensor Range Fault
   - `DTC_P0562`: System Undervoltage (< 8.5V)
   - `DTC_U0100`: CAN Communication Loss / Heartbeat Timeout

---

### 4. Memory Footprint and Execution Efficiency

- Zero dynamic heap allocation (`malloc` free) during runtime.
- Deterministic 10ms execution cycle rate (100 Hz loop).
- Clean C ABI boundary enabling sub-millisecond execution of 25+ integration scenarios in < 0.5 seconds on host PC.

