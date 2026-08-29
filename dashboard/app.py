"""
Executive Dashboard — Streamlit.

Run with:  streamlit run dashboard/app.py
(needs the FastAPI backend running on localhost:8000 first)
"""

import requests
import streamlit as st
import pandas as pd

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Clinical Intelligence Platform", layout="wide")
st.title("Clinical Intelligence Platform — Executive Dashboard")
st.caption("AI-047 — synthetic data")

# ---- Patient selector ----
try:
    patients = requests.get(f"{API_BASE}/patients", params={"limit": 50}).json()
except requests.exceptions.ConnectionError:
    st.error("Can't reach the backend. Start it with: uvicorn app.main:app --reload")
    st.stop()

if not patients:
    st.warning("No patients found. Run the ETL scripts first (see README).")
    st.stop()

patient_options = {f"{p['name']} ({p['id'][:8]})": p["id"] for p in patients}
selected_label = st.sidebar.selectbox("Select patient", list(patient_options.keys()))
selected_id = patient_options[selected_label]

tab1, tab2, tab3, tab4 = st.tabs(
    ["Patient Overview", "Risk & Alerts", "Population Risk", "Hospital Operations"]
)

# ---- Tab 1: Patient overview ----
with tab1:
    detail = requests.get(f"{API_BASE}/patients/{selected_id}").json()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(detail["name"])
        st.write(f"Gender: {detail['gender']}  |  DOB: {detail['birth_date']}")
        st.write("**Conditions:**", ", ".join(detail["conditions"]) or "None recorded")
        st.write("**Allergies:**", ", ".join(detail["allergies"]) or "None recorded")
    with col2:
        st.write("**Current medications:**")
        for med in detail["medications"]:
            st.write(f"- {med}")

    st.divider()
    st.subheader("Ask the AI Copilot")
    question = st.text_input("Question", placeholder="Summarize this patient's history")
    if st.button("Ask") and question:
        with st.spinner("Thinking..."):
            resp = requests.post(
                f"{API_BASE}/copilot/ask",
                json={"patient_id": selected_id, "question": question},
            ).json()
        st.write(resp["answer"])
        st.caption(
            f"Confidence: {resp['confidence']:.0%} | "
            f"Evidence: {', '.join(resp['evidence_sources'])}"
        )

# ---- Tab 2: Risk & alerts for selected patient ----
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Risk scores")
        try:
            risks = requests.get(f"{API_BASE}/risk/{selected_id}/all").json()
            for r in risks:
                label = r["risk_type"].replace("_", " ").title()
                value = f"{r['score']:.0%}" if r["unit"] == "probability" else f"{r['score']:.1f} days"
                st.metric(label, value)
                st.caption("Top factors: " + "; ".join(r["top_factors"]))
        except Exception as e:
            st.info("Risk models not trained yet — run app/ml/train.py first.")

    with col2:
        st.subheader("Alerts")
        alerts = requests.get(f"{API_BASE}/alerts/{selected_id}").json()
        if alerts["alert_count"] == 0:
            st.success("No active alerts")
        for a in alerts["alerts"]:
            severity_color = {"high": "🔴", "moderate": "🟡", "low": "🟢"}.get(a["severity"], "⚪")
            st.write(f"{severity_color} **{a['type'].replace('_', ' ').title()}**: {a['detail']}")

# ---- Tab 3: Population-level risk distribution ----
with tab3:
    st.subheader("Readmission risk distribution (sample of patients)")
    if st.button("Compute population risk (may take a moment)"):
        scores = []
        for p in patients[:20]:
            try:
                r = requests.get(f"{API_BASE}/risk/{p['id']}/readmission").json()
                if "score" in r:
                    scores.append(r["score"])
            except Exception:
                continue
        if scores:
            df = pd.DataFrame({"readmission_risk": scores})
            st.bar_chart(df["readmission_risk"].value_counts(bins=5).sort_index())
            st.metric("Average readmission risk", f"{sum(scores)/len(scores):.0%}")
        else:
            st.info("No scores available — train the models first.")

# ---- Tab 4: Hospital operations (simulated) ----
with tab4:
    st.info("These metrics are simulated — no real hospital operations data source exists in this project's scope.")
    ops = requests.get(f"{API_BASE}/hospital-ops/summary").json()
    df = pd.DataFrame(ops["departments"])
    st.dataframe(df, use_container_width=True)
    col1, col2 = st.columns(2)
    col1.metric("ED Load", f"{ops['ed_load_pct']}%")
    col2.metric("Equipment Utilization", f"{ops['equipment_utilization_pct']}%")
