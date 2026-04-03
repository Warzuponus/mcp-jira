"""
Tests for the Jira client implementation.
"""

import pytest
from unittest.mock import AsyncMock
from mcp_jira.jira_client import JiraClient
from mcp_jira.types import IssueType, Priority, JiraError


@pytest.mark.asyncio
async def test_create_issue(mock_jira_client):
    """Test creating a Jira issue"""
    result = await mock_jira_client.create_issue(
        summary="Test Issue",
        description="Test Description",
        issue_type=IssueType.STORY,
        priority=Priority.HIGH,
        story_points=5
    )
    assert result == "TEST-1"


@pytest.mark.asyncio
async def test_get_sprint(mock_jira_client):
    """Test getting sprint details"""
    sprint = await mock_jira_client.get_sprint(1)
    assert sprint.id == 1
    assert sprint.name == "Test Sprint"
    assert sprint.status.value == "active"


@pytest.mark.asyncio
async def test_get_sprint_issues(mock_jira_client, sample_issue):
    """Test getting sprint issues"""
    issues = await mock_jira_client.get_sprint_issues(1)
    assert len(issues) > 0
    assert issues[0].key == sample_issue.key
    assert issues[0].summary == sample_issue.summary


@pytest.mark.asyncio
async def test_get_backlog_issues(mock_jira_client):
    """Test getting backlog issues"""
    issues = await mock_jira_client.get_backlog_issues()
    assert len(issues) > 0
    assert all(isinstance(issue.key, str) for issue in issues)


@pytest.mark.asyncio
async def test_search_issues(mock_jira_client):
    """Test searching issues"""
    jql = 'project = "TEST"'
    issues = await mock_jira_client.search_issues(jql)
    assert len(issues) > 0
    assert all(hasattr(issue, 'key') for issue in issues)


@pytest.mark.asyncio
async def test_get_issue_history(mock_jira_client):
    """Test getting issue history"""
    history = await mock_jira_client.get_issue_history("TEST-1")
    assert isinstance(history, list)
    assert len(history) > 0
    assert history[0]["from_status"] == "To Do"
    assert history[0]["to_status"] == "In Progress"


@pytest.mark.asyncio
async def test_get_assigned_issues(mock_jira_client):
    """Test getting assigned issues"""
    issues = await mock_jira_client.get_assigned_issues("test_user")
    assert len(issues) > 0
    assert all(hasattr(issue, 'assignee') for issue in issues)


@pytest.mark.asyncio
async def test_error_handling(mock_jira_client, mock_response):
    """Test error handling on API failures"""
    # Replace the request mock to return error status
    async def error_request(method, url, **kwargs):
        return mock_response(500, {"error": "Internal Server Error"})

    mock_jira_client.session.request = AsyncMock(side_effect=error_request)

    with pytest.raises(JiraError):
        await mock_jira_client.create_issue(
            summary="Test Issue",
            description="Test Description",
            issue_type=IssueType.STORY,
            priority=Priority.HIGH
        )


@pytest.mark.asyncio
async def test_active_sprint(mock_jira_client):
    """Test getting the active sprint"""
    sprint = await mock_jira_client.get_active_sprint()
    assert sprint is not None
    assert sprint.name == "Test Sprint"
    assert sprint.status.value == "active"


@pytest.mark.asyncio
async def test_active_sprint_no_board(test_settings):
    """Test get_active_sprint returns None when no board is configured"""
    client = JiraClient(test_settings)
    client.board_id = None
    result = await client.get_active_sprint()
    assert result is None


@pytest.mark.asyncio
async def test_issue_status_custom(mock_jira_client, mock_response):
    """Test that custom/unknown Jira statuses are handled gracefully"""
    async def custom_status_request(method, url, **kwargs):
        return mock_response(200, {
            "issues": [{
                "key": "TEST-99",
                "fields": {
                    "summary": "Custom status issue",
                    "issuetype": {"name": "Story"},
                    "priority": {"name": "Medium"},
                    "status": {"name": "Awaiting QA"},
                    "created": "2024-01-08T10:00:00.000Z",
                    "updated": "2024-01-08T10:00:00.000Z",
                    "customfield_10026": 3
                }
            }]
        })

    mock_jira_client.session.request = AsyncMock(side_effect=custom_status_request)

    issues = await mock_jira_client.search_issues("project = TEST")
    assert len(issues) == 1
    assert issues[0].status.value == "Custom"
    assert issues[0].status_name == "Awaiting QA"