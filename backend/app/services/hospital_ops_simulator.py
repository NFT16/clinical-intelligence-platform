"""
Hospital Operations Intelligence — SIMULATED DATA.

No dataset (Synthea included) provides real bed occupancy, staffing, or
equipment utilization — that data lives in hospital-internal systems no
demo project has access to. Rather than skip this module (it's explicitly
listed in the brief), we generate plausible, clearly-labeled synthetic
metrics. Say this out loud in your presentation — it's an honest scoping
decision, not a hidden gap.
"""

import random
from datetime import datetime

DEPARTMENTS = ["ICU", "Emergency", "General Ward", "Surgery", "Pediatrics", "Cardiology"]


def get_hospital_ops_summary(seed: int | None = None) -> dict:
    rng = random.Random(seed or datetime.now().hour)  # changes through the day, stable within an hour

    departments = []
    for dept in DEPARTMENTS:
        capacity = rng.randint(20, 80)
        occupied = rng.randint(int(capacity * 0.4), capacity)
        departments.append({
            "department": dept,
            "capacity": capacity,
            "occupied": occupied,
            "occupancy_pct": round(occupied / capacity * 100, 1),
            "staff_on_duty": rng.randint(5, 25),
        })

    return {
        "simulated": True,
        "note": "Synthetic operational metrics — no real hospital ops data source exists for this project.",
        "generated_at": datetime.now().isoformat(),
        "departments": departments,
        "ed_load_pct": rng.randint(40, 95),
        "equipment_utilization_pct": rng.randint(30, 85),
    }
