"""
Tests for the Jira client implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp_jira.jira_client import JiraClient
from mcp_jira.types import IssueType, Priority

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_create_issue(mock_session_class, mock_jira_client):
    """Test creating a Jira issue"""
    # Set up mock session
    mock_session = MagicMock()
    mock_session_class.return_value.__aenter__.return_value = mock_session
    mock_session_class.return_value.__aexit__.return_value = None

    # Mock the POST response
    mock_response = MagicMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={"key": "TEST-1"})
    mock_session.post.return_value.__aenter__.return_value = mock_response
    mock_session.post.return_value.__aexit__.return_value = None

    result = await mock_jira_client.create_issue(
        summary="Test Issue",
        description="Test Description",
        issue_type=IssueType.STORY,
        priority=Priority.HIGH,
        story_points=5
    )
    assert result == "TEST-1"

@pytest.mark.asyncio
async def test_get_sprint(mock_jira_client, sample_sprint):
    """Test getting sprint details"""
    sprint = await mock_jira_client.get_sprint(1)
    assert sprint.id == 1
    assert sprint.name == "Test Sprint"

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

@pytest.mark.asyncio
async def test_get_assigned_issues(mock_jira_client):
    """Test getting assigned issues"""
    issues = await mock_jira_client.get_assigned_issues("test_user")
    assert len(issues) > 0
    assert all(hasattr(issue, 'assignee') for issue in issues)

@pytest.mark.asyncio
async def test_error_handling(mock_jira_client, mock_response):
    """Test error handling"""
    # Mock error response
    mock_jira_client._session.post = mock_response(500, {"error": "Test error"})
    
    with pytest.raises(Exception):
        await mock_jira_client.create_issue(
            summary="Test Issue",
            description="Test Description",
            issue_type=IssueType.STORY,
            priority=Priority.HIGH
        )