"""
Tests for the simple MCP server implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from mcp_jira.simple_mcp_server import (
    list_tools, call_tool, handle_create_issue, 
    handle_search_issues, handle_sprint_status
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
        mock_sprint.status.value = "Active"
        mock_sprint.goal = "Complete features"
        mock_sprint.start_date = None
        mock_sprint.end_date = None
        
        # Mock issues
        mock_issue = Mock()
        mock_issue.story_points = 5
        mock_issue.status.value = "Done"
        
        mock_client.get_active_sprint = AsyncMock(return_value=mock_sprint)
        mock_client.get_sprint_issues = AsyncMock(return_value=[mock_issue])
        
        args = {}
        result = await handle_sprint_status(args)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Test Sprint" in result[0].text
        assert "📊" in result[0].text

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