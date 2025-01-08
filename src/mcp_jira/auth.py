"""
Simple API token authentication for MCP Jira.
"""

from fastapi import Security, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from typing import Optional
from pydantic import BaseModel

class TokenAuth:
    """Simple API token authentication"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

    async def verify_token(
        self, 
        token: str = Security(APIKeyHeader(name="X-API-Key"))
    ) -> bool:
        """Verify the API token"""
        if token != self.api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )
        return True

# Helper function to create dependency
def get_auth_handler(settings) -> TokenAuth:
    return TokenAuth(settings.api_key)

# Usage in FastAPI endpoints:
"""
@app.post("/issues")
async def create_issue(
    issue: IssueCreate,
    auth: bool = Depends(auth_handler.verify_token),
    jira_client: JiraClient = Depends(get_jira_client)
):
    # Only authenticated requests can access this endpoint
    ...
"""
