# Virtual ECU Firmware Verification & Validation (V&V) Automation Lab

[![Language](https://img.shields.io/badge/Language-C11-blue)](https://en.wikipedia.org/wiki/C_(programming_language))
[![Python](https://img.shields.io/badge/Python-3.14-yellow)](https://www.python.org/)
[![Testing](https://img.shields.io/badge/Testing-Pytest-green)](https://pytest.org/)
[![Platform](https://img.shields.io/badge/Platform-Software%20in%20the%20Loop-lightgrey)](https://en.wikipedia.org/wiki/Software-in-the-loop)
[![Status](https://img.shields.io/badge/Project-Completed-success)]()

## Project Overview

The **Virtual ECU Firmware Verification & Validation Automation Lab** is a software-based automotive embedded systems project developed to demonstrate ECU firmware testing, validation, fault detection, diagnostic handling, and automated test reporting.

The project simulates an Electronic Control Unit (ECU) environment using Embedded C and Python. It follows a Software-in-the-Loop (SIL) approach, allowing firmware behavior to be tested without requiring physical ECU hardware.

The system integrates C-based ECU firmware with Python-based automated testing using `ctypes` and `pytest`.

The primary objective is to demonstrate practical concepts used in automotive embedded software verification, including state machine validation, sensor monitoring, fault injection, diagnostic handling, and safety-oriented testing.

## Project Objectives

- Develop a software-based Virtual ECU using Embedded C.
- Implement ECU operating states and state transitions.
- Simulate automotive sensor inputs.
- Validate sensor signals and detect abnormal conditions.
- Implement fault injection and fault recovery scenarios.
- Demonstrate automotive diagnostic concepts based on ISO 14229 (UDS).
- Demonstrate safety-oriented development and testing concepts inspired by ISO 26262.
- Automate firmware verification using Python and Pytest.
- Generate machine-readable and human-readable test reports.

## System Architecture

The project follows a layered Software-in-the-Loop architecture.

```text
          Python Automation Layer
                    |
                    v
             Pytest Framework
                    |
                    v
              Python ctypes
                    |
                    v
           C Firmware Interface
                    |
                    v
             Virtual ECU Core
                    |
       +------------+------------+
       |            |            |
       v            v            v
   ECU State    Sensor        Diagnostic
   Machine      Monitoring    Handling
       |            |            |
       +------------+------------+
                    |
                    v
             Fault Injection
                    |
                    v
             Test Results
                    |
          +---------+---------+
          |         |         |
          v         v         v
         JSON      CSV       HTML
                 Reports    Dashboard
```

## Key Features

### 1. Virtual ECU Firmware

- Developed using Embedded C11.
- Simulates ECU firmware behavior without physical hardware.
- Provides a C-based firmware interface for Python integration.
- Supports software-level validation of ECU behavior.

### 2. ECU State Machine

The Virtual ECU implements seven operating states:

| State | Description |
|---|---|
| OFF | ECU is powered off |
| INIT | ECU initialization |
| STANDBY | ECU is initialized and waiting |
| RUNNING | Normal operating condition |
| DEGRADED | Limited operation due to detected faults |
| ERROR | Critical error condition |
| SHUTDOWN | ECU shutdown sequence |

The state machine is used to validate operating conditions, transitions, and fault-related behavior.

### 3. Virtual Sensor Simulation

The project simulates automotive sensor inputs to validate ECU responses.

Sensor validation includes:

- Sensor input monitoring.
- Signal range validation.
- Abnormal input detection.
- Dual-channel Throttle Position Sensor (TPS) plausibility checking.
- Fault condition simulation.

### 4. Fault Injection and Handling

Fault injection is used to simulate abnormal operating conditions and evaluate firmware responses.

Examples include:

- Sensor signal faults.
- Out-of-range sensor values.
- TPS channel mismatch.
- Diagnostic fault conditions.
- Fault detection and recovery scenarios.

### 5. Automotive Diagnostic Concepts

The project demonstrates selected diagnostic concepts based on **ISO 14229 – Unified Diagnostic Services (UDS)**.

Diagnostic-related functionality includes:

- Fault condition detection.
- Diagnostic status handling.
- Fault monitoring.
- ECU response validation.

This is a software simulation of selected diagnostic concepts, not a complete implementation or certification of the ISO 14229 standard.

### 6. Safety-Oriented Validation

The project demonstrates selected safety-oriented verification concepts inspired by **ISO 26262**, including:

- Fault detection.
- Sensor plausibility monitoring.
- Safe-state-oriented behavior.
- Degraded operating conditions.
- Fault response validation.

These are educational and simulation-level demonstrations of safety concepts. The project is not ISO 26262 certified and does not establish an ASIL-B compliance claim.

## Technology Stack

| Technology | Purpose |
|---|---|
| Embedded C11 | Virtual ECU firmware development |
| Python 3.14 | Test automation |
| Pytest | Automated test execution |
| ctypes | Python-to-C firmware integration |
| JSON | Structured test result reporting |
| CSV | Tabular test reporting |
| HTML | Test dashboard and report visualization |
| Git & GitHub | Version control and project hosting |
| Vercel | Static dashboard deployment |

## Testing and Validation

The project uses Python-based automated testing to validate the Virtual ECU firmware.

The test automation framework communicates with the C firmware through the Python `ctypes` interface.

Validation areas include:

- ECU initialization and state transitions.
- Normal operating behavior.
- Sensor input validation.
- Dual-channel TPS plausibility.
- Fault injection.
- Diagnostic behavior.
- Error handling and recovery.
- ECU shutdown behavior.

### Test Execution

Run the automated test suite using:

```bash
pytest -v
```

### Test Results

**Reported test execution: 25 / 25 tests passed.**

| Metric | Result |
|---|---:|
| Total Test Cases | 25 |
| Passed | 25 |
| Failed | 0 |
| Pass Rate | 100% |

The results above represent the reported execution of this project’s automated test suite. They do not represent complete automotive system validation or certification.

## Test Reports and Dashboard

The project generates test reports in three formats:

| Report Format | Purpose |
|---|---|
| JSON | Machine-readable test results |
| CSV | Tabular test results |
| HTML | Browser-based test report dashboard |

The HTML dashboard provides a visual representation of the generated test results.

**Live Dashboard:**  
[Open Virtual ECU Test Dashboard](YOUR_VERCEL_URL/dashboard.html)

> Replace `YOUR_VERCEL_URL` with the actual Vercel deployment URL after deployment.

## Repository Structure

The project is organized into firmware, automation, reporting, and documentation components.

```text
virtual-ecu-firmware-vnv-lab/
│
├── firmware/
│   └── C-based Virtual ECU firmware
│
├── tests/
│   └── Python Pytest automation tests
│
├── reports/
│   ├── JSON test reports
│   ├── CSV test reports
│   └── html/
│       └── dashboard.html
│
├── README.md
└── .gitignore
```

*Note: This is a logical overview. Keep the actual folder and file names consistent with the files in the GitHub repository.*

## How to Run the Project

### Prerequisites

Install the following:

- Python 3.14
- GCC or another compatible C compiler
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/sargunan-c/virtual-ecu-firmware-vnv-lab.git
```

### Step 2: Navigate to the Project

```bash
cd virtual-ecu-firmware-vnv-lab
```

### Step 3: Install Pytest

```bash
python -m pip install pytest
```

### Step 4: Run Automated Tests

```bash
pytest -v
```

### Step 5: View the Test Dashboard

Open the generated HTML dashboard in a web browser.

The dashboard is available at:

```text
reports/html/dashboard.html
```

The exact report-generation and firmware-build commands depend on the scripts included in the repository.

## Requirements Traceability

The project demonstrates a basic verification workflow connecting firmware behavior with test scenarios.

| Area | Verification Focus |
|---|---|
| ECU State Machine | State transition validation |
| Sensor Monitoring | Input range and signal validation |
| TPS Plausibility | Dual-channel signal comparison |
| Fault Injection | Abnormal condition simulation |
| Diagnostics | Selected UDS diagnostic concepts |
| Safety Behavior | Fault response and degraded-state validation |
| Test Automation | Repeatable Pytest execution |
| Reporting | JSON, CSV, and HTML report generation |

## Skills Demonstrated

- Embedded C Programming (C11)
- Automotive Embedded Systems
- ECU Firmware Verification and Validation
- Software-in-the-Loop (SIL) Testing
- Python Test Automation
- Pytest Framework
- C and Python Integration using ctypes
- Finite State Machine (FSM) Validation
- Sensor Signal Validation
- Fault Injection Testing
- Automotive Diagnostic Concepts (ISO 14229 / UDS)
- Functional Safety Concepts (ISO 26262)
- Test Reporting and Documentation
- Git and GitHub
- Vercel Static Deployment

## Project Highlights

- Developed a software-based Virtual ECU using Embedded C11.
- Integrated C firmware with Python automation using ctypes.
- Implemented a seven-state ECU state machine.
- Simulated automotive sensor inputs and TPS plausibility checks.
- Demonstrated fault injection and diagnostic handling.
- Automated firmware validation using Pytest.
- Reported 25 successful automated test cases.
- Generated JSON, CSV, and HTML test reports.
- Deployed the HTML dashboard for browser-based viewing.

## Disclaimer

This project is an educational and portfolio demonstration of automotive embedded firmware verification and validation concepts.

It is a software-only simulation and has not been validated on physical automotive ECU hardware.

The project does not claim ISO 26262 certification, ASIL-B certification, production readiness, or complete compliance with ISO 14229.

## Author

**Sargunan C**

GitHub:  
https://github.com/sargunan-c

---

*Virtual ECU Firmware Verification & Validation Automation Lab – Embedded C | Python | Pytest | Automotive Software Testing*
