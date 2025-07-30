"""Configuration settings for the Avatar application."""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application settings
    APP_NAME: str = "Avatar"
    DEBUG: bool = False
    
    # Mistral AI settings
    MISTRAL_API_KEY: str = Field(..., validation_alias="MISTRAL_API_KEY")
    MISTRAL_MODEL: str = Field("mistral-medium", validation_alias="MISTRAL_MODEL")
    MISTRAL_TEMPERATURE: float = 0.7
    MISTRAL_MAX_TOKENS: int = 2000
    
    # MCP Server settings
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8000
    
    # Kimble API settings
    KIMBLE_BASE_URL: str = Field(..., validation_alias="KIMBLE_BASE_URL")
    KIMBLE_API_KEY: str = Field(..., validation_alias="KIMBLE_API_KEY")
    
    @field_validator("MISTRAL_API_KEY")
    @classmethod
    def validate_mistral_key(cls, v: Optional[str]) -> str:
        """Validate that Mistral API key is set."""
        if not v:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        return v

# Create settings instance
settings = Settings()
