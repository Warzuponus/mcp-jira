from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    JIRA_URL: str
    JIRA_USERNAME: str
    JIRA_API_TOKEN: str
    PROJECT_KEY: Optional[str] = None
    DEFAULT_BOARD_ID: Optional[int] = None

    class Config:
        env_file = ".env"

settings = Settings()
