from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for runtime configuration.

    All values are overridable via environment variables / .env — see .env.example.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://nexusmind:nexusmind@localhost:5432/nexusmind"

    # Auth
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    # Model providers
    # "ollama" runs fully local/offline with no API key and no billing —
    # the default so the app works out of the box. Set to "anthropic" or
    # "openai" (and fill in the matching key) to use a hosted model instead.
    llm_provider: str = "ollama"  # "anthropic" | "openai" | "ollama"
    embedding_provider: str = "ollama"  # "openai" | "ollama"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768  # must match embedding_model's output size
    llm_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    # Retrieval
    retrieval_top_k: int = 4

    # CORS
    frontend_origin: str = "http://localhost:3000"

    # GitHub live connector
    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    github_sync_enabled: bool = False
    github_poll_interval_seconds: int = 180
    # ACL applied to every chunk ingested from GitHub (comma-separated)
    github_allowed_roles: str = "dev,management"
    github_allowed_groups: str = "eng-payments"
    # Caps keep a single poll bounded regardless of repo size
    github_max_doc_files: int = 40
    github_max_code_files: int = 60
    github_max_issues: int = 50
    github_max_prs: int = 50


settings = Settings()
