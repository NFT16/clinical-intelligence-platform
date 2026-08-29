"""
Reads clinical data from Postgres and builds the Neo4j knowledge graph.

Graph model (start simple, extend later):
  (:Patient)-[:HAS_CONDITION]->(:Condition)
  (:Patient)-[:PRESCRIBED]->(:Medication)
  (:Patient)-[:HAD_LAB]->(:LabResult)
  (:Patient)-[:HAS_ALLERGY]->(:Allergy)
  (:Patient)-[:HAD_ENCOUNTER]->(:Encounter)

Run this AFTER load_synthea_to_postgres.py.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.db.postgres import SessionLocal
from app.db.neo4j_client import neo4j_client
from app.models.patient import Patient


def push_patient_node(tx_client, patient: Patient):
    tx_client.run_query(
        """
        MERGE (p:Patient {id: $id})
        SET p.name = $name, p.gender = $gender, p.birth_date = $birth_date
        """,
        {
            "id": patient.id,
            "name": f"{patient.first_name} {patient.last_name}",
            "gender": patient.gender,
            "birth_date": str(patient.birth_date),
        },
    )

    for condition in patient.conditions:
        tx_client.run_query(
            """
            MERGE (c:Condition {code: $code})
            SET c.description = $description
            WITH c
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_CONDITION]->(c)
            """,
            {
                "code": condition.code,
                "description": condition.description,
                "patient_id": patient.id,
            },
        )

    for med in patient.medications:
        tx_client.run_query(
            """
            MERGE (m:Medication {code: $code})
            SET m.description = $description
            WITH m
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:PRESCRIBED]->(m)
            """,
            {
                "code": med.code,
                "description": med.description,
                "patient_id": patient.id,
            },
        )

    for allergy in patient.allergies:
        tx_client.run_query(
            """
            MERGE (a:Allergy {code: $code})
            SET a.description = $description
            WITH a
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:HAS_ALLERGY]->(a)
            """,
            {
                "code": allergy.code,
                "description": allergy.description,
                "patient_id": patient.id,
            },
        )

    for procedure in patient.procedures:
        tx_client.run_query(
            """
            MERGE (proc:Procedure {code: $code})
            SET proc.description = $description
            WITH proc
            MATCH (p:Patient {id: $patient_id})
            MERGE (p)-[:UNDERWENT]->(proc)
            """,
            {
                "code": procedure.code,
                "description": procedure.description,
                "patient_id": patient.id,
            },
        )
        if procedure.provider_id:
            tx_client.run_query(
                """
                MERGE (doc:Physician {id: $provider_id})
                WITH doc
                MATCH (proc:Procedure {code: $code})
                MERGE (doc)-[:PERFORMED]->(proc)
                """,
                {"provider_id": procedure.provider_id, "code": procedure.code},
            )

    for encounter in patient.encounters:
        if encounter.provider_id:
            tx_client.run_query(
                """
                MERGE (doc:Physician {id: $provider_id})
                WITH doc
                MATCH (p:Patient {id: $patient_id})
                MERGE (doc)-[:TREATED]->(p)
                """,
                {"provider_id": encounter.provider_id, "patient_id": patient.id},
            )


def main():
    db = SessionLocal()
    try:
        patients = db.query(Patient).all()

        # Get patient IDs that already exist in Neo4j
        existing = neo4j_client.run_query(
            "MATCH (p:Patient) RETURN p.id AS id"
        )

        existing_ids = {row["id"] for row in existing}

        missing_patients = [
            patient for patient in patients
            if patient.id not in existing_ids
        ]

        print(f"Patients in source database: {len(patients)}")
        print(f"Patients already in Neo4j: {len(existing_ids)}")
        print(f"Patients still to process: {len(missing_patients)}")

        if not missing_patients:
            print("All patients are already in the Neo4j knowledge graph.")
            return

        for i, patient in enumerate(missing_patients, 1):
            print(
                f"Processing missing patient "
                f"{i}/{len(missing_patients)}: {patient.id}"
            )

            push_patient_node(neo4j_client, patient)

        print("Knowledge graph build complete.")

    finally:
        db.close()
        neo4j_client.close()


if __name__ == "__main__":
    main()
