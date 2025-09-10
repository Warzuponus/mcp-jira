"""
Configuration management for MCP Jira.
Handles environment variables, settings validation, and configuration defaults.
"""

from pydantic import HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings
from typing import Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    """
    Configuration settings for the MCP Jira application.
    Uses Pydantic for validation and environment variable loading.
    """
    # Jira Configuration
    jira_url: HttpUrl
    jira_username: str
    jira_api_token: SecretStr
    project_key: str
    default_board_id: Optional[int] = None

    # Application Settings
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Sprint Defaults
    default_sprint_length: int = 14  # days
    story_points_field: str = "customfield_10026"  # Default story points field
    max_sprint_items: int = 50
    
    # Performance Settings
    jira_request_timeout: int = 30  # seconds
    cache_ttl: int = 300  # seconds
    max_concurrent_requests: int = 10
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return upper_v

    @field_validator("jira_url")
    @classmethod
    def validate_jira_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure Jira URL is properly formatted"""
        url_str = str(v)
        if not url_str.endswith("/"):
            url_str += "/"
        return HttpUrl(url_str)

@lru_cache()
def get_settings() -> Settings:
    """
    Get settings with LRU cache to avoid reading environment variables multiple times.
    """
    return Settings()

def initialize_logging(settings: Settings) -> None:
    """Initialize logging configuration"""
    import logging
    
    logging.basicConfig(
        level=settings.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Example .env file template
ENV_TEMPLATE = """
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your.email@domain.com
JIRA_API_TOKEN=your_api_token
PROJECT_KEY=PROJ
DEFAULT_BOARD_ID=123

# Application Settings
DEBUG_MODE=false
LOG_LEVEL=INFO
"""

def generate_env_template() -> str:
    """Generate a template .env file"""
    return ENV_TEMPLATE.strip()
