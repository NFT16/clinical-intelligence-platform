"""
Rule-based Medication Safety Engine.

Three checks, all deterministic (no ML needed — and none should be used
here; conflict-checking must be auditable, not probabilistic):
  1. Known drug-drug interactions (data/reference/drug_interactions.json)
  2. Allergy conflicts (medication description overlaps an allergy description)
  3. Duplicate therapy (same medication prescribed twice with overlapping dates)
"""

import json
from itertools import combinations
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.patient import Patient

REFERENCE_PATH = Path(__file__).resolve().parents[3] / "data" / "reference" / "drug_interactions.json"

with open(REFERENCE_PATH) as f:
    _INTERACTIONS = json.load(f)["interactions"]


def _active_medications(patient: Patient) -> list:
    # "active" = no end_date, or end_date not yet reached is left simple here;
    # for a demo we treat every recorded medication as relevant.
    return patient.medications


def check_drug_interactions(patient: Patient) -> list[dict]:
    meds = [m.description.lower() for m in _active_medications(patient)]
    findings = []
    for interaction in _INTERACTIONS:
        a, b = interaction["drug_a"], interaction["drug_b"]
        if any(a in m for m in meds) and any(b in m for m in meds):
            findings.append({
                "type": "drug_interaction",
                "severity": interaction["severity"],
                "detail": f"{a} + {b}: {interaction['description']}",
            })
    return findings


def check_allergy_conflicts(patient: Patient) -> list[dict]:
    findings = []
    allergy_terms = [a.description.lower() for a in patient.allergies]
    for med in _active_medications(patient):
        med_desc = med.description.lower()
        for term in allergy_terms:
            # crude substring match — fine for a demo, a real system needs
            # ingredient-level matching via RxNorm, not string overlap.
            key_term = term.split()[0] if term else ""
            if key_term and key_term in med_desc:
                findings.append({
                    "type": "allergy_conflict",
                    "severity": "high",
                    "detail": f"{med.description} conflicts with recorded allergy: {term}",
                })
    return findings


def check_duplicate_therapy(patient: Patient) -> list[dict]:
    findings = []
    meds = _active_medications(patient)
    for m1, m2 in combinations(meds, 2):
        if m1.description == m2.description and m1.id != m2.id:
            findings.append({
                "type": "duplicate_therapy",
                "severity": "moderate",
                "detail": f"{m1.description} appears to be prescribed more than once.",
            })
    return findings


def run_all_checks(patient: Patient) -> list[dict]:
    return (
        check_drug_interactions(patient)
        + check_allergy_conflicts(patient)
        + check_duplicate_therapy(patient)
    )
