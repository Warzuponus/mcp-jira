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
def mock_jira_client(test_settings, mock_response):
    """Create a mock Jira client"""
    client = JiraClient(test_settings)

    # Mock the entire session to prevent HTTP calls
    client.session = MagicMock()
    client.session.closed = False

    # Mock all HTTP methods to return successful responses
    def mock_get(*args, **kwargs):
        url = str(args[0])
        
        # Changelog
        if "changelog" in url:
            return mock_response(200, {
                "values": [
                    {
                        "id": "10001",
                        "author": {
                            "displayName": "Test User",
                            "accountId": "test_user"
                        },
                        "created": "2024-01-08T12:00:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fieldtype": "jira",
                                "from": "10000",
                                "fromString": "To Do",
                                "to": "3",
                                "toString": "In Progress"
                            }
                        ]
                    }
                ]
            })

        # Sprint Issues (must check before generic sprint)
        elif "sprint" in url and "issue" in url:
            return mock_response(200, {
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
            })

        # Sprint details
        elif "sprint" in url:
            return mock_response(200, {
                "id": 1,
                "name": "Test Sprint",
                "goal": "Test Goal",
                "state": "Active",
                "startDate": "2024-01-08T00:00:00.000Z",
                "endDate": "2024-01-22T00:00:00.000Z"
            })

        # Issue details or search
        elif "issue" in url:
            return mock_response(200, {
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
            })
        
        return mock_response(200, {})

    def mock_post(*args, **kwargs):
        # Mock issue creation
        if "issue" in str(args[0]) and "search" not in str(args[0]):
            return mock_response(201, {"key": "TEST-1"})
        # Mock search
        else:
            return mock_response(200, {
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
            })

    client.session.get = MagicMock(side_effect=mock_get)
    client.session.post = MagicMock(side_effect=mock_post)

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