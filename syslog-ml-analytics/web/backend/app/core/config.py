from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SYSLOG_ML_", extra="ignore")

    # Postgres holds the web app's own state: users, SNMP credentials, ML
    # feedback/corrections. Kept separate from ClickHouse, which stays a
    # write-heavy, read-mostly store for the log events themselves.
    database_url: str = "postgresql+asyncpg://syslog_ml:syslog_ml@localhost:5432/syslog_ml"

    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123

    jwt_secret: str = "changeme-generate-a-real-secret-with-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8

    # Dev-only default. Generate a real one with:
    #   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    credential_encryption_key: str = "l_4kEGewM6ILrPN6XDKa9tW2gW7FxcG4pisE1GkoL8M="

    cors_origins: list[str] = ["http://localhost:5173"]

    # Log Assistant: semantic search (OpenSearch, populated by
    # ml/log_assistant_indexer.py) + an LLM (Ollama) that answers questions
    # grounded only in the retrieved log excerpts. Both assumed reachable,
    # unauthenticated, on localhost -- same trust boundary as ClickHouse.
    ollama_host: str = "http://localhost:11434"
    # CPU-only inference, same constraint ml/train_classifier.py's docstring
    # explains for the TF-IDF classifier -- a small instruct model, not a
    # heavyweight one.
    ollama_chat_model: str = "llama3.2:3b-instruct-q4_K_M"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_num_predict: int = 400
    ollama_timeout_seconds: float = 120.0

    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_index: str = "syslog_logs"


settings = Settings()
