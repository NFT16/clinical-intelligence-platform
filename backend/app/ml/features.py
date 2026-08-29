"""
Builds a feature table for risk modeling, one row per encounter.

Kept deliberately simple: counts and flags computed from data that Synthea
always generates (encounters, conditions, medications), so this works
regardless of which optional Synthea modules were enabled.
"""

from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.models.patient import Patient, Encounter, Condition, Medication


def _age_at(birth_date, at_date) -> float:
    if birth_date is None or at_date is None:
        return 0.0
    return (pd.Timestamp(at_date) - pd.Timestamp(birth_date)).days / 365.25


def build_feature_table(db: Session) -> pd.DataFrame:
    """
    One row per encounter with:
      - age at encounter, gender
      - prior_condition_count, prior_medication_count (up to this encounter)
      - prior_encounter_count (how many times seen before)
      - days_since_last_encounter
      - length_of_stay_days (target for the LOS model)
      - readmitted_30d (target for the readmission model — next inpatient
        encounter for this patient starts within 30 days of this one ending)
    """
    encounters = (
        db.query(Encounter)
        .order_by(Encounter.patient_id, Encounter.start_time)
        .all()
    )

    rows = []
    patient_history: dict[str, list[Encounter]] = {}

    for enc in encounters:
        patient = enc.patient
        history = patient_history.setdefault(enc.patient_id, [])

        prior_conditions = sum(
            1 for c in patient.conditions
            if c.onset_date and enc.start_time and c.onset_date <= enc.start_time.date()
        )
        prior_meds = sum(
            1 for m in patient.medications
            if m.start_date and enc.start_time and m.start_date <= enc.start_time.date()
        )
        days_since_last = None
        if history:
            last = history[-1]
            if last.end_time and enc.start_time:
                days_since_last = (enc.start_time - last.end_time).days

        los_days = None
        if enc.start_time and enc.end_time:
            los_days = max((enc.end_time - enc.start_time).total_seconds() / 86400, 0)

        # readmission label: next inpatient encounter within 30 days of this one ending
        readmitted = 0
        idx = history and len(history) or 0
        future_encounters = [
            e for e in encounters
            if e.patient_id == enc.patient_id and e.start_time and enc.end_time
            and e.start_time > enc.end_time
        ]
        if future_encounters:
            next_enc = min(future_encounters, key=lambda e: e.start_time)
            gap_days = (next_enc.start_time - enc.end_time).days
            if enc.encounter_type == "inpatient" and gap_days <= 30:
                readmitted = 1

        rows.append({
            "encounter_id": enc.id,
            "patient_id": enc.patient_id,
            "age": _age_at(patient.birth_date, enc.start_time),
            "gender": patient.gender,
            "encounter_type": enc.encounter_type,
            "prior_condition_count": prior_conditions,
            "prior_medication_count": prior_meds,
            "prior_encounter_count": len(history),
            "days_since_last_encounter": days_since_last if days_since_last is not None else -1,
            "length_of_stay_days": los_days,
            "readmitted_30d": readmitted,
        })

        history.append(enc)

    return pd.DataFrame(rows)
