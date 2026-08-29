from sqlalchemy import Column, String, Date, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship

from app.db.postgres import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)  # Synthea patient UUID
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(Date)
    gender = Column(String)
    race = Column(String)

    encounters = relationship("Encounter", back_populates="patient")
    conditions = relationship("Condition", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    lab_results = relationship("LabResult", back_populates="patient")
    allergies = relationship("Allergy", back_populates="patient")
    procedures = relationship("Procedure", back_populates="patient")


class Provider(Base):
    __tablename__ = "providers"

    id = Column(String, primary_key=True)
    name = Column(String)
    specialty = Column(String)

    encounters = relationship("Encounter", back_populates="provider")
    procedures = relationship("Procedure", back_populates="provider")


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    provider_id = Column(String, ForeignKey("providers.id"), nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    encounter_type = Column(String)  # e.g. inpatient, outpatient, emergency
    reason = Column(String)

    patient = relationship("Patient", back_populates="encounters")
    provider = relationship("Provider", back_populates="encounters")
    procedures = relationship("Procedure", back_populates="encounter")


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"), nullable=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=True)
    code = Column(String)          # SNOMED procedure code
    description = Column(String)
    date = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="procedures")
    encounter = relationship("Encounter", back_populates="procedures")
    provider = relationship("Provider", back_populates="procedures")


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"), nullable=True)
    code = Column(String)          # SNOMED/ICD code
    description = Column(String)
    onset_date = Column(Date)

    patient = relationship("Patient", back_populates="conditions")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"), nullable=True)
    code = Column(String)          # RxNorm code
    description = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    dosage = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="medications")


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    encounter_id = Column(String, ForeignKey("encounters.id"), nullable=True)
    code = Column(String)          # LOINC code
    description = Column(String)
    value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    result_date = Column(DateTime)

    patient = relationship("Patient", back_populates="lab_results")


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    code = Column(String)
    description = Column(String)

    patient = relationship("Patient", back_populates="allergies")
