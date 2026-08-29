"""
Multi-agent orchestrator using LangGraph. This is the piece that satisfies
the brief's "Multi-Agent AI" and "Multi-Agent AI Workflow" requirements
"""

from typing import TypedDict

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agents.router import classify_intent
from app.agents import graph_agent, risk_agent, retrieval_agent


class CopilotState(TypedDict):
    patient_id: str
    question: str
    intent: str
    answer: str
    evidence_sources: list[str]
    confidence: float


def _route_node(state: CopilotState) -> dict:
    return {"intent": classify_intent(state["question"])}


def _history_node(state: CopilotState) -> dict:
    return graph_agent.summarize_patient_history(state["patient_id"])


def _general_node(state: CopilotState) -> dict:
    return retrieval_agent.answer_from_notes(state["question"], state["patient_id"])


def _make_risk_node(db: Session):
    def _risk_node(state: CopilotState) -> dict:
        q = state["question"].lower()
        risk_type = "length_of_stay" if ("length of stay" in q or " los" in q) else "readmission"
        return risk_agent.explain_risk(db, state["patient_id"], risk_type)
    return _risk_node


def build_orchestrator(db: Session):
    graph = StateGraph(CopilotState)

    graph.add_node("route", _route_node)
    graph.add_node("history", _history_node)
    graph.add_node("risk", _make_risk_node(db))
    graph.add_node("general", _general_node)

    graph.set_entry_point("route")
    graph.add_conditional_edges(
        "route",
        lambda state: state["intent"],
        {"history": "history", "risk": "risk", "general": "general"},
    )
    graph.add_edge("history", END)
    graph.add_edge("risk", END)
    graph.add_edge("general", END)

    return graph.compile()


def run_copilot(db: Session, patient_id: str, question: str) -> dict:
    orchestrator = build_orchestrator(db)
    initial_state: CopilotState = {
        "patient_id": patient_id,
        "question": question,
        "intent": "",
        "answer": "",
        "evidence_sources": [],
        "confidence": 0.0,
    }
    final_state = orchestrator.invoke(initial_state)
    return {
        "answer": final_state["answer"],
        "evidence_sources": final_state["evidence_sources"],
        "confidence": final_state["confidence"],
    }
