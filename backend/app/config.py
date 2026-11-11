import os
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator

# Determine base directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    SUPABASE_URL: str | None = Field(default=None, description="Supabase project URL")
    SUPABASE_ANON_KEY: SecretStr | None = Field(default=None, description="Supabase public anonymous key")
    SUPABASE_SERVICE_ROLE_KEY: SecretStr | None = Field(default=None, description="Supabase service role secret key")
    SUPABASE_STORAGE_BUCKET: str = Field("evidence", description="Supabase storage bucket for evidence")
    PORT: int = Field(8000, description="Server port")
    HOST: str = Field("0.0.0.0", description="Server host")
    ENVIRONMENT: str = Field("development", description="Environment: development, staging, production")
    ALLOW_DEV_AUTH_HEADERS: bool = Field(False, description="Allow mock identity headers in local development only")
    ALLOWED_ORIGINS: list[str] = Field(default_factory=list, description="Explicit browser origins allowed by CORS")
    OPENROUTER_API_KEY: SecretStr | None = Field(default=None, description="OpenRouter API key for conversation responses")
    CONVERSATION_MODEL: str | None = Field(default=None, description="OpenRouter model used for patient conversations")
    OPENROUTER_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0, le=180)
    GEMINI_API_KEY: SecretStr | None = Field(default=None, description="Gemini API key")
    GROQ_API_KEY: SecretStr | None = Field(default=None, description="Groq API key")
    GEMINI_CONVERSATION_API_KEY: SecretStr | None = None
    GROQ_CONVERSATION_API_KEY: SecretStr | None = None
    GEMINI_ORCHESTRATOR_API_KEY: SecretStr | None = None
    GROQ_ORCHESTRATOR_API_KEY: SecretStr | None = None
    GEMINI_VERIFICATION_API_KEY: SecretStr | None = None
    GROQ_VERIFICATION_API_KEY: SecretStr | None = None
    SARVAM_API_KEY: SecretStr | None = Field(default=None, description="Sarvam speech API key")
    AI_CONVERSATION_PROVIDERS: str = "gemini,groq"
    AI_ORCHESTRATOR_PROVIDERS: str = "gemini,groq"
    AI_VERIFICATION_PROVIDERS: str = "gemini,groq"
    GEMINI_CONVERSATION_MODEL: str | None = None
    GROQ_CONVERSATION_MODEL: str | None = None
    GEMINI_ORCHESTRATOR_MODEL: str | None = None
    GROQ_ORCHESTRATOR_MODEL: str | None = None
    GEMINI_VERIFICATION_MODEL: str | None = None
    GROQ_VERIFICATION_MODEL: str | None = None
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Storage limits
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_MIME_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    @field_validator("ENVIRONMENT")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_allowed_origins(cls, value: list[str]) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in value if origin.strip()]
        if "*" in origins:
            raise ValueError("ALLOWED_ORIGINS must contain explicit origins; wildcards are not allowed")
        # On local development, browsers treat localhost and 127.0.0.1 as
        # different origins. Pair those loopback spellings on the same port
        # so either Vite URL works without permitting arbitrary origins.
        paired = list(origins)
        for origin in origins:
            if origin.startswith("http://localhost:"):
                paired.append(origin.replace("http://localhost:", "http://127.0.0.1:", 1))
            elif origin.startswith("http://127.0.0.1:"):
                paired.append(origin.replace("http://127.0.0.1:", "http://localhost:", 1))
        return list(dict.fromkeys(paired))

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.ENVIRONMENT.lower() == "production" and self.ALLOW_DEV_AUTH_HEADERS:
            raise ValueError("ALLOW_DEV_AUTH_HEADERS cannot be enabled in production")
        if self.ENVIRONMENT.lower() == "production" and not self.ALLOWED_ORIGINS:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin in production")
        return self

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", Path.cwd() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

