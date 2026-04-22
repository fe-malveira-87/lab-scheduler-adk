from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    ocr_mcp_host: str = "0.0.0.0"
    ocr_mcp_port: int = 8001

    rag_mcp_host: str = "0.0.0.0"
    rag_mcp_port: int = 8002

    chroma_host: str = "localhost"
    chroma_port: int = 8003
    chroma_collection: str = "lab_exams"


@lru_cache
def get_settings() -> Settings:
    return Settings()
