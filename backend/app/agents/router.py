
RISK_KEYWORDS = ["risk", "readmission", "readmit", "length of stay", "los", "deteriorat"]
HISTORY_KEYWORDS = ["history", "summarize", "summary", "conditions", "medications", "allergies", "graph"]


def classify_intent(question: str) -> str:
    q = question.lower()
    if any(k in q for k in RISK_KEYWORDS):
        return "risk"
    if any(k in q for k in HISTORY_KEYWORDS):
        return "history"
    return "general"  # falls through to the RAG retrieval agent
