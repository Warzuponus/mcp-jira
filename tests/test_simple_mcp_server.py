"""
Tests for the simple MCP server implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from mcp_jira.simple_mcp_server import (
    list_tools, call_tool, handle_create_issue,
    handle_search_issues, handle_sprint_status,
    handle_team_workload, handle_standup_report
)
from mcp_jira.types import IssueType, Priority, Issue, Sprint, IssueStatus, SprintStatus
from mcp.types import Tool, TextContent


@pytest.mark.asyncio
async def test_list_tools():
    """Test that tools are properly listed"""
    tools = await list_tools()

    assert len(tools) == 5
    tool_names = [tool.name for tool in tools]

    expected_tools = [
        "create_issue", "search_issues", "get_sprint_status",
        "get_team_workload", "generate_standup_report"
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names


@pytest.mark.asyncio
async def test_tool_descriptions_are_detailed():
    """Test that tool descriptions are rich and informative"""
    tools = await list_tools()
    for tool in tools:
        # Every description should be at least 50 chars (not just "Create a new Jira issue")
        assert len(tool.description) >= 50, f"Tool '{tool.name}' has a too-short description"


@pytest.mark.asyncio
async def test_create_issue_tool():
    """Test create_issue tool"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.create_issue = AsyncMock(return_value="TEST-123")

        args = {
            "summary": "Test Issue",
            "description": "Test Description",
            "issue_type": "Story",
            "priority": "High"
        }

        result = await handle_create_issue(args)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "TEST-123" in result[0].text
        assert "✅" in result[0].text


@pytest.mark.asyncio
async def test_search_issues_tool():
    """Test search_issues tool"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        # Mock issue data
        mock_issue = Mock()
        mock_issue.key = "TEST-1"
        mock_issue.summary = "Test Issue"
        mock_issue.status.value = "In Progress"
        mock_issue.status_name = "In Progress"
        mock_issue.priority.value = "High"
        mock_issue.assignee = None
        mock_issue.story_points = 5

        mock_client.search_issues = AsyncMock(return_value=[mock_issue])

        args = {"jql": "project = TEST"}
        result = await handle_search_issues(args)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "TEST-1" in result[0].text
        assert "Test Issue" in result[0].text


@pytest.mark.asyncio
async def test_search_issues_no_results():
    """Test search_issues with no results"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.search_issues = AsyncMock(return_value=[])

        args = {"jql": "project = EMPTY"}
        result = await handle_search_issues(args)

        assert len(result) == 1
        assert "No issues found" in result[0].text


@pytest.mark.asyncio
async def test_sprint_status_tool():
    """Test get_sprint_status tool"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        # Mock sprint data
        mock_sprint = Mock()
        mock_sprint.id = 1
        mock_sprint.name = "Test Sprint"
        mock_sprint.status.value = "active"
        mock_sprint.goal = "Complete features"
        mock_sprint.start_date = None
        mock_sprint.end_date = None

        # Mock issues
        mock_issue = Mock()
        mock_issue.story_points = 5
        mock_issue.status.value = "Done"
        mock_issue.status_name = "Done"

        mock_client.get_active_sprint = AsyncMock(return_value=mock_sprint)
        mock_client.get_sprint_issues = AsyncMock(return_value=[mock_issue])

        args = {}
        result = await handle_sprint_status(args)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Test Sprint" in result[0].text
        assert "📊" in result[0].text
        assert "100.0%" in result[0].text


@pytest.mark.asyncio
async def test_sprint_status_no_active_sprint():
    """Test sprint status when no active sprint exists"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.get_active_sprint = AsyncMock(return_value=None)

        result = await handle_sprint_status({})
        assert "No active sprint found" in result[0].text


@pytest.mark.asyncio
async def test_team_workload_tool():
    """Test get_team_workload tool"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_issue = Mock()
        mock_issue.story_points = 8
        mock_issue.status.value = "In Progress"

        mock_client.get_assigned_issues = AsyncMock(return_value=[mock_issue])

        args = {"team_members": ["john.doe"]}
        result = await handle_team_workload(args)

        assert len(result) == 1
        assert "john.doe" in result[0].text
        assert "8" in result[0].text  # total points


@pytest.mark.asyncio
async def test_team_workload_error_handling():
    """Test team workload gracefully handles errors for individual members"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.get_assigned_issues = AsyncMock(side_effect=Exception("User not found"))

        args = {"team_members": ["nonexistent_user"]}
        result = await handle_team_workload(args)

        assert "❌" in result[0].text
        assert "Could not fetch data" in result[0].text


@pytest.mark.asyncio
async def test_standup_report_tool():
    """Test generate_standup_report tool"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_sprint = Mock()
        mock_sprint.id = 1
        mock_sprint.name = "Sprint 42"

        mock_issue = Mock()
        mock_issue.story_points = 5
        mock_issue.status.value = "In Progress"
        mock_issue.status_name = "In Progress"
        mock_issue.assignee = Mock()
        mock_issue.assignee.display_name = "John"
        mock_issue.key = "TEST-1"
        mock_issue.summary = "Do something"
        mock_issue.updated_at = datetime.now(timezone.utc)

        mock_client.get_active_sprint = AsyncMock(return_value=mock_sprint)
        mock_client.get_sprint_issues = AsyncMock(return_value=[mock_issue])

        result = await handle_standup_report({})

        assert "Sprint 42" in result[0].text
        assert "🌅" in result[0].text


@pytest.mark.asyncio
async def test_standup_report_no_sprint():
    """Test standup report when no active sprint exists"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.get_active_sprint = AsyncMock(return_value=None)

        result = await handle_standup_report({})
        assert "No active sprint found" in result[0].text


@pytest.mark.asyncio
async def test_standup_report_zero_points():
    """Test standup report handles zero total points without division-by-zero"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_sprint = Mock()
        mock_sprint.id = 1
        mock_sprint.name = "Sprint Zero"

        mock_issue = Mock()
        mock_issue.story_points = None  # no points assigned
        mock_issue.status.value = "To Do"
        mock_issue.status_name = "To Do"
        mock_issue.assignee = None
        mock_issue.key = "TEST-1"
        mock_issue.summary = "Unpointed"
        mock_issue.updated_at = datetime.now(timezone.utc)

        mock_client.get_active_sprint = AsyncMock(return_value=mock_sprint)
        mock_client.get_sprint_issues = AsyncMock(return_value=[mock_issue])

        # This should NOT raise a ZeroDivisionError
        result = await handle_standup_report({})
        assert "0.0%" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_unknown():
    """Test calling an unknown tool"""
    with patch('mcp_jira.simple_mcp_server.jira_client', Mock()):
        result = await call_tool("unknown_tool", {})

        assert len(result) == 1
        assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_no_client():
    """Test calling tool when client is not initialized"""
    with patch('mcp_jira.simple_mcp_server.jira_client', None):
        result = await call_tool("create_issue", {})

        assert len(result) == 1
        assert "Jira client not initialized" in result[0].text