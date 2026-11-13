"""
Telemetry Logger for Automotive ECU Verification & Validation.
Records high-rate cycle snapshots and exports to CSV / JSON for audit and report generation.
"""

import csv
import json
import os
from pathlib import Path

class TelemetryLogger:
    def __init__(self, log_name: str = "run_telemetry"):
        self.log_name = log_name
        self.records = []

    def log_cycle(self, telemetry: dict):
        flattened = {
            "cycle": telemetry["cycle_count"],
            "uptime_ms": telemetry["uptime_ms"],
            "state": telemetry["state_name"],
            "coolant_c": telemetry["inputs"]["coolant_temp_c"],
            "tps1_pct": telemetry["inputs"]["tps1_pct"],
            "tps2_pct": telemetry["inputs"]["tps2_pct"],
            "map_kpa": telemetry["inputs"]["map_kpa"],
            "vbatt_v": telemetry["inputs"]["battery_voltage_v"],
            "rpm": telemetry["inputs"]["rpm"],
            "fuel_pw_ms": telemetry["actuators"]["fuel_pw_ms"],
            "spark_deg": telemetry["actuators"]["spark_advance_deg"],
            "fan_state": telemetry["actuators"]["fan_state"],
            "mil_lamp": telemetry["actuators"]["mil_lamp"],
            "throttle_cmd_pct": telemetry["actuators"]["throttle_cmd_pct"],
            "active_dtcs": ";".join(telemetry["active_dtcs"]) if telemetry["active_dtcs"] else "NONE"
        }
        self.records.append(flattened)

    def export_csv(self, filepath: str = None) -> str:
        if filepath is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            filepath = str(base_dir / "reports" / "csv" / f"{self.log_name}.csv")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if not self.records:
            return filepath

        fieldnames = list(self.records[0].keys())
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.records)

        return filepath

    def export_json(self, filepath: str = None) -> str:
        if filepath is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            filepath = str(base_dir / "reports" / "json" / f"{self.log_name}.json")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)

        return filepath
