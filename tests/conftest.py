"""
PyTest configuration and fixtures for MCP Jira tests.
"""

import pytest
from typing import Dict, Any
import aiohttp
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from mcp_jira.config import Settings
from mcp_jira.jira_client import JiraClient
from mcp_jira.types import Issue, Sprint, TeamMember, IssueType, Priority, IssueStatus

@pytest.fixture
def test_settings():
    """Provide test settings"""
    # Mock environment variables for testing
    import os
    os.environ["JIRA_URL"] = "https://test-jira.example.com"
    os.environ["JIRA_USERNAME"] = "test_user"
    os.environ["JIRA_API_TOKEN"] = "test_token"
    os.environ["PROJECT_KEY"] = "TEST"
    os.environ["DEFAULT_BOARD_ID"] = "1"

    return Settings()

@pytest.fixture
def mock_response():
    """Create a mock aiohttp response"""
    class MockResponse:
        def __init__(self, status: int, data: Dict[str, Any]):
            self.status = status
            self._data = data

        async def json(self):
            return self._data

        async def text(self):
            return str(self._data)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockResponse

@pytest.fixture
def mock_jira_client(test_settings):
    """Create a mock Jira client"""
    client = JiraClient(test_settings)

    # Mock the entire session to prevent HTTP calls
    client._session = MagicMock()

    # Mock all HTTP methods to return successful responses
    async def mock_get(*args, **kwargs):
        # Mock sprint response
        if "sprint" in str(args[0]):
            return MagicMock(status=200, json=AsyncMock(return_value={
                "id": 1,
                "name": "Test Sprint",
                "goal": "Test Goal",
                "state": "active",
                "startDate": "2024-01-08T00:00:00.000Z",
                "endDate": "2024-01-22T00:00:00.000Z"
            }))
        # Mock issue response
        elif "issue" in str(args[0]):
            return MagicMock(status=200, json=AsyncMock(return_value={
                "issues": [{
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Test Issue",
                        "description": "Test Description",
                        "issuetype": {"name": "Story"},
                        "priority": {"name": "High"},
                        "status": {"name": "To Do"},
                        "assignee": {
                            "name": "test_user",
                            "displayName": "Test User",
                            "emailAddress": "test@example.com"
                        },
                        "created": "2024-01-08T10:00:00.000Z",
                        "updated": "2024-01-08T10:00:00.000Z",
                        "customfield_10026": 5
                    }
                }]
            }))

    async def mock_post(*args, **kwargs):
        # Mock issue creation
        if "issue" in str(args[0]):
            return MagicMock(status=201, json=AsyncMock(return_value={"key": "TEST-1"}))
        # Mock search
        else:
            return MagicMock(status=200, json=AsyncMock(return_value={
                "issues": [{
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Test Issue",
                        "description": "Test Description",
                        "issuetype": {"name": "Story"},
                        "priority": {"name": "High"},
                        "status": {"name": "To Do"},
                        "assignee": {
                            "name": "test_user",
                            "displayName": "Test User",
                            "emailAddress": "test@example.com"
                        },
                        "created": "2024-01-08T10:00:00.000Z",
                        "updated": "2024-01-08T10:00:00.000Z",
                        "customfield_10026": 5
                    }
                }]
            }))

    client._session.get = AsyncMock(side_effect=mock_get)
    client._session.post = AsyncMock(side_effect=mock_post)

    return client

@pytest.fixture
def sample_issue():
    """Provide a sample issue"""
    return Issue(
            key="TEST-1",
            summary="Test Issue",
            description="Test Description",
            issue_type=IssueType.STORY,
            priority=Priority.HIGH,
            status=IssueStatus.TODO,
            assignee=TeamMember(
                username="test_user",
                display_name="Test User",
                email="test@example.com",
                role="Developer"
            ),
            story_points=5,
            labels=[],
            components=[],
            created_at=datetime.fromisoformat("2024-01-08T10:00:00.000"),
            updated_at=datetime.fromisoformat("2024-01-08T10:00:00.000"),
            blocked_by=[],
            blocks=[]
        )

@pytest.fixture
def sample_sprint():
    """Provide a sample sprint"""
    return {
        "id": 1,
        "name": "Test Sprint",
        "goal": "Test Goal",
        "state": "active",
        "startDate": "2024-01-08T00:00:00.000Z",
        "endDate": "2024-01-22T00:00:00.000Z"
    }