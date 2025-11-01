"""Application configuration management using Pydantic settings."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        anthropic_api_key: API key for Anthropic Claude
        openai_api_key: API key for OpenAI (for embeddings)
        claude_model: Claude model to use for generation
        claude_temperature: Temperature for Claude generation (0-1)
        claude_max_tokens: Maximum tokens for Claude response
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required API Keys
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    openai_api_key: Optional[str] = Field(
        None, description="OpenAI API key (for embeddings in Week 2)"
    )

    # Claude Generation Settings
    claude_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude model for flashcard generation",
    )
    claude_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for generation (0=deterministic, 1=creative)",
    )
    claude_max_tokens: int = Field(
        default=1024,
        gt=0,
        description="Maximum tokens in Claude response",
    )

    # Application Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # ChromaDB Settings (for Week 2)
    chroma_db_path: str = Field(
        default="./chroma_db",
        description="Path to ChromaDB storage",
    )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton.

    Returns:
        Settings instance loaded from environment

    Raises:
        ValidationError: If required settings are missing or invalid
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
