from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str = Field(default="")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="qwen2.5:3b")
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    embedding_model: str = Field(default="qwen2.5:3b")

    chroma_persist_dir: str = Field(default="./data/chromadb")
    graph_persist_dir: str = Field(default="./data/graph")

    redis_url: Optional[str] = Field(default=None)
    neo4j_uri: Optional[str] = Field(default=None)
    neo4j_user: Optional[str] = Field(default=None)
    neo4j_password: Optional[str] = Field(default=None)

    secret_key: str = Field(default="ensam-agent-os-secret")
    rate_limit_rpm: int = Field(default=60)
    rate_limit_tpm: int = Field(default=100000)

    groq_cost_per_1k_input: float = Field(default=0.00059)
    groq_cost_per_1k_output: float = Field(default=0.00079)

    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)

    max_retries: int = Field(default=3)
    request_timeout: float = Field(default=600.0)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
