# Clinical Intelligence Platform

An AI-powered clinical decision support system that unifies patient records, predicts clinical risk, checks medication safety, and answers clinical questions through a multi-agent AI copilot, built on a synthetic patient population for demonstration purposes.

## Overview

The Clinical Intelligence Platform integrates fragmented patient data (encounters, conditions, medications, lab results, procedures, and providers) into a single system that supports clinical decision-making through machine learning, a knowledge graph, and a retrieval-augmented AI assistant. It is built as a demonstration of enterprise clinical AI system design, scaled to a synthetic dataset of 228 patients (15,000+ encounters).

## Features

- **Unified Patient Data Model** : patients, encounters, conditions, medications, lab results, allergies, procedures, and providers in a single relational schema.
- **Clinical Knowledge Graph** : a Neo4j graph linking patients to conditions, medications, allergies, procedures, and treating physicians, enabling relationship-based queries.
- **Risk Prediction Engine** : XGBoost models predicting 30-day readmission risk (classification) and expected length of stay (regression), with SHAP-based explanations for every prediction.
- **Medication Safety Engine** : rule-based detection of drug-drug interactions, allergy conflicts, and duplicate therapy.
- **AI Clinical Copilot** : a multi-agent system (LangGraph) that routes clinical questions to a knowledge-graph agent, a risk-explanation agent, or a retrieval-augmented (RAG) agent over clinical notes, with every response grounded in evidence sources and a confidence score.
- **Alert Center** : aggregates high-risk patients, medication conflicts, and critical lab values into a single feed.
- **Hospital Operations Dashboard** : department-level capacity and utilization metrics.
- **Executive Dashboard** : a Streamlit interface surfacing patient records, risk scores, alerts, population-level risk distribution, and the AI copilot.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Relational data | SQLAlchemy, SQLite / PostgreSQL |
| Knowledge graph | Neo4j |
| Machine learning | scikit-learn, XGBoost, SHAP |
| AI / RAG | OpenAI, ChromaDB, LangGraph |
| Dashboard | Streamlit |
| Synthetic data | [Synthea](https://github.com/synthetichealth/synthea) |

## Dataset

Patient data is generated with Synthea, an open-source synthetic patient generator that produces realistic, clinically coherent records with no real protected health information. The demo dataset used in this project contains:

| Entity | Count |
|---|---|
| Patients | 228 |
| Encounters | 15,330 |
| Conditions | 17,734 |
| Medications | 15,253 |
| Lab results | 126,497 |
| Procedures | 43,053 |
| Providers | 432 |
| Allergies | 191 |

## Architecture

```
Synthea (synthetic EHR data)
        │
        ▼
   ETL pipeline
   ┌────┴────┐
   ▼         ▼
SQLite    Neo4j (knowledge graph)
   │         │
   ▼         ▼
Risk models   Graph agent
(XGBoost +    │
 SHAP)        │
   │          │
   ▼          ▼
Risk agent   LangGraph orchestrator ──▶ Retrieval agent (RAG)
   │                  │                       ▲
   └──────────────────┼───────────────────────┘
                       ▼                  Chroma vector store ◀── Clinical notes
                 FastAPI endpoints
                       │
                       ▼
              Streamlit dashboard
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a full component breakdown and design rationale.

## Project Structure

```
backend/app/
  models/       SQLAlchemy models — Patient, Encounter, Condition, Medication, LabResult, Allergy, Provider, Procedure
  db/           Database and Neo4j client setup
  core/         Application configuration
  ml/           Feature engineering, model training, and inference for the risk engine
  services/     Medication safety rule engine, hospital operations metrics
  agents/       Knowledge-graph agent, risk agent, retrieval agent, and the LangGraph orchestrator
  rag/          Vector store for clinical note retrieval
  api/          FastAPI routers — patients, risk, medication, alerts, hospital operations, copilot
data/
  etl/          Synthea → database, database → knowledge graph, notes → vector store
  reference/    Drug interaction reference data
dashboard/      Streamlit executive dashboard
docs/           Architecture documentation
```

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/patients` | GET | List patients |
| `/patients/{id}` | GET | Patient detail : demographics, conditions, medications, allergies |
| `/risk/{id}/readmission` | GET | 30-day readmission risk with SHAP factors |
| `/risk/{id}/length-of-stay` | GET | Predicted length of stay with SHAP factors |
| `/risk/{id}/all` | GET | All risk scores for a patient |
| `/medication/{id}/conflicts` | GET | Drug interactions, allergy conflicts, duplicate therapy |
| `/alerts/{id}` | GET | Combined alert feed for a patient |
| `/alerts` | GET | Hospital-wide alert feed |
| `/hospital-ops/summary` | GET | Department-level capacity and utilization |
| `/copilot/ask` | POST | Natural-language clinical Q&A via the multi-agent copilot |

Full interactive documentation is available at `/docs` when the API is running.

## Setup

**Requirements:** Python 3.11, a Neo4j Aura (or self-hosted Neo4j) instance, an OpenAI API key for the copilot's retrieval agent.

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env           # set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY

# Generate synthetic data
git clone https://github.com/synthetichealth/synthea.git
cd synthea && run_synthea.bat -p 200 --exporter.text.export=true

# Load data
python data/etl/load_synthea_to_postgres.py
python data/etl/build_knowledge_graph.py
python data/etl/build_vector_store.py

# Train risk models
cd backend
python -m app.ml.train

# Run
uvicorn app.main:app --reload          # API on localhost:8000
streamlit run dashboard/app.py         # Dashboard
```

## Limitations

This is a demonstration system, not a production clinical tool:

- Risk models are trained on synthetic data with heuristic labels and are not clinically validated.
- Medication interaction data is a small illustrative dataset, not a licensed drug database (e.g., DrugBank, First Databank).
- Hospital operations metrics are simulated, no dataset provides real bed occupancy or staffing data.
- The system is scoped to a demo population; it does not implement high-availability infrastructure, live EHR/HL7/FHIR integration, or production-grade access control and audit logging.

## Acknowledgments

- [Synthea](https://github.com/synthetichealth/synthea) (MITRE) for synthetic patient data generation.
