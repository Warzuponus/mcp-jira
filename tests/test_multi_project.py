
import pytest
from unittest.mock import AsyncMock, patch
from mcp_jira.simple_mcp_server import handle_create_issue, handle_sprint_status
from mcp_jira.types import IssueType, Priority
from mcp.types import TextContent

@pytest.mark.asyncio
async def test_create_issue_with_project_override():
    """Test creating an issue with a specific project key"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.create_issue = AsyncMock(return_value="OPS-101")
        
        args = {
            "summary": "Fix server",
            "description": "It crashed",
            "issue_type": "Bug",
            "priority": "High",
            "project_key": "OPS"
        }
        
        await handle_create_issue(args)
        
        # Verify project_key was passed to client
        mock_client.create_issue.assert_called_once()
        call_kwargs = mock_client.create_issue.call_args.kwargs
        assert call_kwargs["project_key"] == "OPS"
        assert call_kwargs["summary"] == "Fix server"

@pytest.mark.asyncio
async def test_create_issue_without_override():
    """Test creating an issue uses default (None passed to client)"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.create_issue = AsyncMock(return_value="PROJ-101")
        
        args = {
            "summary": "Standard task",
            "description": "Do work",
            "issue_type": "Task",
            "priority": "Medium"
        }
        
        await handle_create_issue(args)
        
        # Verify project_key was NOT passed (or passed as None)
        mock_client.create_issue.assert_called_once()
        call_kwargs = mock_client.create_issue.call_args.kwargs
        assert call_kwargs.get("project_key") is None

@pytest.mark.asyncio
async def test_sprint_status_with_board_override():
    """Test getting sprint status for a specific board"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        # returns None to trigger 'No active sprint' response just to verify call
        mock_client.get_active_sprint = AsyncMock(return_value=None) 
        
        args = {"board_id": 999}
        
        await handle_sprint_status(args)
        
        # Verify board_id was passed to get_active_sprint
        mock_client.get_active_sprint.assert_called_once_with(board_id=999)

@pytest.mark.asyncio
async def test_sprint_status_default():
    """Test getting sprint status without board override"""
    with patch('mcp_jira.simple_mcp_server.jira_client') as mock_client:
        mock_client.get_active_sprint = AsyncMock(return_value=None)
        
        args = {}
        
        await handle_sprint_status(args)
        
        # Verify board_id was passed as None
        mock_client.get_active_sprint.assert_called_once_with(board_id=None)
