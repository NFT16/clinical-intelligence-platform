from pathlib import Path
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{(ROOT_DIR / 'clinical_platform.db').as_posix()}"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "cip_password"
    neo4j_database: str = "neo4j"

    redis_host: str = "localhost"
    redis_port: int = 6379

    openai_api_key: str = ""

    @property
    def postgres_url(self) -> str:
        return self.database_url

    class Config:
        env_file = str(ROOT_DIR / ".env")


settings = Settings()
