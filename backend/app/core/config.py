from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:dev@localhost:5433/inbox"
    openai_api_key: str
    # no default on purpose: a guessable fallback secret would let anyone forge tokens
    jwt_secret: str
    jwt_expire_minutes: int = 60
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    chat_model: str = "gpt-4o-mini"
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 150
    top_k_chunks: int = 4
    min_similarity: float = 0.45


settings = Settings()
