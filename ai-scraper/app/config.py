from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables and defaulted to values in the class if not found in environment variables"""

    # App
    APP_NAME: str = "AI Scraper"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | production

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_scraper"

    # Redis (for future queue)
    REDIS_URL: str = "redis://localhost:6379"

    # AI Providers
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEFAULT_AI_PROVIDER: str = "gemini"  # gemini | groq | ollama
    DEFAULT_AI_MODEL: str = "flash"

    # Scraping
    MAX_CONCURRENT_SCRAPES: int = 10
    SCRAPE_TIMEOUT_MS: int = 30000
    HEADLESS_BROWSER: bool = True

    # Rate Limiting
    AI_REQUESTS_PER_MINUTE: int = 10  # Conservative default (Gemini free = 10 RPM)

    # File Upload
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "output"
    MAX_UPLOAD_SIZE_MB: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
