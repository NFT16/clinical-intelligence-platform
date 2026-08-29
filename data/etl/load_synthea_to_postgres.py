"""
Loads Synthea's CSV output into Postgres.

Setup (run once):
  1. Clone Synthea:  git clone https://github.com/synthetichealth/synthea.git
  2. Generate data:  cd synthea && ./run_synthea -p 500
     (-p 500 = 500 synthetic patients; adjust for your demo size)
  3. CSVs land in synthea/output/csv/ — point SYNTHEA_CSV_DIR below at that folder.

"""

import sys
from pathlib import Path
from datetime import date, datetime

import pandas as pd
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.db.postgres import SessionLocal, Base, engine
from app.models.patient import (
    Patient, Encounter, Condition, Medication, LabResult, Allergy,
    Provider, Procedure,
)

SYNTHEA_CSV_DIR = Path("synthea/output/csv")  
def to_date(value):
    if pd.isna(value) or value == "":
        return None
    return pd.to_datetime(value).date()


def to_datetime(value):
    if pd.isna(value) or value == "":
        return None
    return pd.to_datetime(value).to_pydatetime()

def load_patients(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "patients.csv")
    for _, row in df.iterrows():
        db.merge(
            Patient(
                id=row["Id"],
                first_name=row.get("FIRST", ""),
                last_name=row.get("LAST", ""),
                birth_date=to_date(row.get("BIRTHDATE")),
                gender=row.get("GENDER"),
                race=row.get("RACE"),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} patients")


def load_providers(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "providers.csv")
    for _, row in df.iterrows():
        db.merge(
            Provider(
                id=row["Id"],
                name=row.get("NAME"),
                specialty=row.get("SPECIALITY", row.get("SPECIALTY")),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} providers")


def load_encounters(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "encounters.csv")
    for _, row in df.iterrows():
        db.merge(
            Encounter(
                id=row["Id"],
                patient_id=row["PATIENT"],
                provider_id=row.get("PROVIDER"),
                start_time=to_datetime(row.get("START")),
                end_time=to_datetime(row.get("STOP")),
                encounter_type=row.get("ENCOUNTERCLASS"),
                reason=row.get("REASONDESCRIPTION"),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} encounters")


def load_procedures(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "procedures.csv")
    for _, row in df.iterrows():
        db.merge(
            Procedure(
                id=f"{row['PATIENT']}_{row['CODE']}_{row['START']}_{row.name}",
                patient_id=row["PATIENT"],
                encounter_id=row.get("ENCOUNTER"),
                provider_id=row.get("PROVIDER") if "PROVIDER" in df.columns else None,
                code=row["CODE"],
                description=row["DESCRIPTION"],
                date=to_datetime(row.get("START")),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} procedures")

def load_conditions(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "conditions.csv")
    for _, row in df.iterrows():
        db.merge(
            Condition(
                id=f"{row['PATIENT']}_{row['CODE']}_{row['START']}_{row.name}",
                patient_id=row["PATIENT"],
                encounter_id=row.get("ENCOUNTER"),
                code=row["CODE"],
                description=row["DESCRIPTION"],
                onset_date=to_date(row.get("START")),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} conditions")


def load_medications(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "medications.csv")
    for _, row in df.iterrows():
        db.merge(
            Medication(
                id=f"{row['PATIENT']}_{row['CODE']}_{row['START']}_{row.name}",
                patient_id=row["PATIENT"],
                encounter_id=row.get("ENCOUNTER"),
                code=row["CODE"],
                description=row["DESCRIPTION"],
                start_date=to_date(row.get("START")),
                end_date=to_date(row.get("STOP")),
            )
        )
    db.commit()
    print(f"Loaded {len(df)} medications")


def load_lab_results(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "observations.csv")

    loaded = 0
    skipped = 0

    for idx, row in df.iterrows():
        try:
            value = float(row["VALUE"])
        except (ValueError, TypeError):
            skipped += 1
            continue

        db.merge(
            LabResult(
                id=f"{row['PATIENT']}_{row['CODE']}_{row['DATE']}_{idx}",
                patient_id=row["PATIENT"],
                encounter_id=row.get("ENCOUNTER"),
                code=row["CODE"],
                description=row["DESCRIPTION"],
                value=value,
                unit=row.get("UNITS"),
                result_date=to_datetime(row.get("DATE")),
            )
        )

        loaded += 1

    db.commit()

    print(f"Loaded {loaded} lab results")
    print(f"Skipped {skipped} non-numeric observations")


def load_allergies(db: Session, csv_dir: Path):
    df = pd.read_csv(csv_dir / "allergies.csv")
    for _, row in df.iterrows():
        db.merge(
            Allergy(
                id=f"{row['PATIENT']}_{row['CODE']}",
                patient_id=row["PATIENT"],
                code=row["CODE"],
                description=row["DESCRIPTION"],
            )
        )
    db.commit()
    print(f"Loaded {len(df)} allergies")


def main():
    Base.metadata.create_all(bind=engine)  # creates tables if not present
    db = SessionLocal()
    try:
        load_patients(db, SYNTHEA_CSV_DIR)
        load_providers(db, SYNTHEA_CSV_DIR)
        load_encounters(db, SYNTHEA_CSV_DIR)
        load_conditions(db, SYNTHEA_CSV_DIR)
        load_medications(db, SYNTHEA_CSV_DIR)
        load_lab_results(db, SYNTHEA_CSV_DIR)
        load_allergies(db, SYNTHEA_CSV_DIR)
        load_procedures(db, SYNTHEA_CSV_DIR)
    finally:
        db.close()


if __name__ == "__main__":
    main()
