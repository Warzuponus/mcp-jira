"""
Configuration management for MCP Jira.
Handles environment variables, settings validation, and configuration defaults.
"""

from pydantic import BaseSettings, HttpUrl, SecretStr, validator
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
    default_board_id: int

    # Application Settings
    api_key: SecretStr
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Sprint Defaults
    default_sprint_length: int = 14  # days
    story_points_field: str = "customfield_10026"  # Default story points field
    max_sprint_items: int = 50
    
    # Performance Settings
    jira_request_timeout: int = 30  # seconds
    cache_ttl: int = 300  # seconds
    max_concurrent_requests: int = 10
    
    # Metrics Configuration
    velocity_window: int = 3  # Number of sprints to consider for velocity
    risk_threshold_high: float = 0.8
    risk_threshold_medium: float = 0.5
    
    # Feature Flags
    enable_workload_balancing: bool = True
    enable_risk_analysis: bool = True
    enable_automated_planning: bool = True
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return upper_v

    @validator("jira_url")
    def validate_jira_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure Jira URL ends with /rest/api/2"""
        if not str(v).endswith("/"):
            v = HttpUrl(str(v) + "/", scheme=v.scheme)
        return v

class DevelopmentSettings(Settings):
    """Development environment settings"""
    class Config:
        env_prefix = "DEV_"

class ProductionSettings(Settings):
    """Production environment settings"""
    debug_mode: bool = False
    
    class Config:
        env_prefix = "PROD_"

class TestSettings(Settings):
    """Test environment settings"""
    debug_mode: bool = True
    
    class Config:
        env_prefix = "TEST_"

@lru_cache()
def get_settings() -> Settings:
    """
    Get the appropriate settings based on the environment.
    Uses LRU cache to avoid reading environment variables multiple times.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "test": TestSettings
    }
    
    settings_class = settings_map.get(environment, Settings)
    return settings_class()

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
API_KEY=your_secure_api_key
DEBUG_MODE=false
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Feature Flags
ENABLE_WORKLOAD_BALANCING=true
ENABLE_RISK_ANALYSIS=true
ENABLE_AUTOMATED_PLANNING=true
"""

def generate_env_template() -> str:
    """Generate a template .env file"""
    return ENV_TEMPLATE.strip()
