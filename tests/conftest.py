"""
PyTest configuration and fixtures for MCP Jira tests.
"""

import pytest
from typing import Dict, Any
import aiohttp
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from mcp_jira.config import Settings
from mcp_jira.jira_client import JiraClient
from mcp_jira.types import Issue, Sprint, TeamMember, IssueType, Priority, IssueStatus, SprintStatus

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
            self.headers = {}

        async def json(self):
            return self._data

        async def text(self):
            return str(self._data)

        def release(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockResponse

@pytest.fixture
def mock_jira_client(test_settings, mock_response):
    """Create a mock Jira client with mocked HTTP methods."""
    client = JiraClient(test_settings)

    # Mock the session so no real HTTP calls happen
    mock_session = MagicMock()
    mock_session.closed = False
    client.session = mock_session

    # Build a request dispatcher that mimics aiohttp's session.request()
    async def mock_request(method: str, url: str, **kwargs):
        url_str = str(url)

        if method.upper() == "GET":
            # Changelog
            if "changelog" in url_str:
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
            elif "sprint" in url_str and "issue" in url_str:
                return mock_response(200, {
                    "total": 1,
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

            # Board sprints
            elif "board" in url_str and "sprint" in url_str:
                return mock_response(200, {
                    "values": [{
                        "id": 1,
                        "name": "Test Sprint",
                        "goal": "Test Goal",
                        "state": "active",
                        "startDate": "2024-01-08T00:00:00.000Z",
                        "endDate": "2024-01-22T00:00:00.000Z"
                    }]
                })

            # Sprint details
            elif "sprint" in url_str:
                return mock_response(200, {
                    "id": 1,
                    "name": "Test Sprint",
                    "goal": "Test Goal",
                    "state": "active",
                    "startDate": "2024-01-08T00:00:00.000Z",
                    "endDate": "2024-01-22T00:00:00.000Z"
                })

            # Issue details or search
            elif "issue" in url_str:
                return mock_response(200, {
                    "total": 1,
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

        elif method.upper() == "POST":
            # Mock issue creation
            if "issue" in url_str and "search" not in url_str:
                return mock_response(201, {"key": "TEST-1"})
            # Mock search (search/jql uses cursor pagination — no total field)
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

        return mock_response(200, {})

    mock_session.request = AsyncMock(side_effect=mock_request)

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
            status_name="To Do",
            assignee=TeamMember(
                username="test_user",
                display_name="Test User",
                email="test@example.com",
                role="Developer"
            ),
            story_points=5,
            labels=[],
            components=[],
            created_at=datetime(2024, 1, 8, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 8, 10, 0, 0, tzinfo=timezone.utc),
            blocked_by=[],
            blocks=[]
        )

@pytest.fixture
def sample_sprint():
    """Provide a sample sprint (matches Jira API lowercase state values)"""
    return {
        "id": 1,
        "name": "Test Sprint",
        "goal": "Test Goal",
        "state": "active",
        "startDate": "2024-01-08T00:00:00.000Z",
        "endDate": "2024-01-22T00:00:00.000Z"
    }