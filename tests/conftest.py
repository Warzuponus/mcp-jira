"""
PyTest configuration and fixtures for MCP Jira tests.
"""

import pytest
from typing import Dict, Any
import aiohttp
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from mcp_jira.config import Settings, TestSettings
from mcp_jira.jira_client import JiraClient
from mcp_jira.scrum_master import ScrumMaster
from mcp_jira.types import Issue, Sprint, TeamMember, IssueType, Priority, IssueStatus

@pytest.fixture
def test_settings():
    """Provide test settings"""
    return TestSettings(
        jira_url="https://test-jira.example.com",
        jira_username="test_user",
        jira_api_token="test_token",
        project_key="TEST",
        default_board_id=1,
        api_key="test_api_key"
    )

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
def mock_jira_client(test_settings, mock_response):
    """Create a mock Jira client"""
    client = JiraClient(test_settings)
    
    # Mock sample issue
    sample_issue = {
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
    }

    # Mock responses
    async def mock_get(*args, **kwargs):
        return mock_response(200, {"issues": [sample_issue]})

    async def mock_post(*args, **kwargs):
        return mock_response(201, {"key": "TEST-1"})

    # Replace client's session with mock
    client._session = MagicMock()
    client._session.get = AsyncMock(side_effect=mock_get)
    client._session.post = AsyncMock(side_effect=mock_post)

    return client

@pytest.fixture
def mock_scrum_master(mock_jira_client):
    """Create a mock Scrum Master"""
    return ScrumMaster(mock_jira_client)

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
            email="test@example.com"
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