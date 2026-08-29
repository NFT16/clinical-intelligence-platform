from neo4j import GraphDatabase

from app.core.config import settings


class Neo4jClient:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self):
        self._driver.close()

    def run_query(self, query: str, params: dict | None = None) -> list[dict]:
        with self._driver.session(database=settings.neo4j_database) as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def get_patient_graph(self, patient_id: str) -> list[dict]:
        """
        Pull everything connected to a patient: conditions, medications,
        labs, encounters. Used by the copilot to answer
        'summarize this patient's history' style questions.
        """
        query = """
        MATCH (p:Patient {id: $patient_id})-[r]-(n)
        RETURN type(r) AS relationship, labels(n) AS node_type,
               n AS node
        """
        return self.run_query(query, {"patient_id": patient_id})


neo4j_client = Neo4jClient()
