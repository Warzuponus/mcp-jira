
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, Mock
import sys
from pathlib import Path
import os
from mcp_jira.simple_mcp_server import main
from mcp_jira.config import Settings

from mcp_jira.__main__ import check_env_file

def test_check_env_file_found():
    """Test check_env_file returns path when found"""
    with patch("mcp_jira.__main__.Path") as MockPathClass:
        mock_instance = MagicMock()
        mock_instance.exists.return_value = True
        
        # recursive mocking for parents and division
        mock_instance.parent = mock_instance
        mock_instance.__truediv__.return_value = mock_instance
        
        MockPathClass.return_value = mock_instance
        
        result = check_env_file()
        assert result is not None
        assert result.exists() is True

def test_check_env_file_not_found():
    """Test check_env_file returns None when not found and prints error"""
    with patch("mcp_jira.__main__.Path") as MockPathClass:
        mock_instance = MagicMock()
        mock_instance.exists.return_value = False
        
        # recursive mocking for parents and division
        mock_instance.parent = mock_instance
        mock_instance.__truediv__.return_value = mock_instance
        
        MockPathClass.return_value = mock_instance
        
        # We need check_env_file to FAIL to find anything
        result = check_env_file()
        assert result is None

@pytest.mark.asyncio
async def test_server_main_lifecycle():
    """Test server main loop lifecycle and cleanup"""
    
    with patch("mcp_jira.simple_mcp_server.get_settings", return_value=Settings(
        jira_url="https://test.atlassian.net",
        jira_username="user",
        jira_api_token="token",
        project_key="TEST"
    )):
        with patch("mcp_jira.simple_mcp_server.JiraClient") as MockJiraClient:
            mock_client_instance = AsyncMock()
            MockJiraClient.return_value = mock_client_instance
            
            with patch("mcp_jira.simple_mcp_server.stdio_server") as mock_stdio:
                # Mock context manager
                mock_stdio.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())
                mock_stdio.return_value.__aexit__.return_value = None
                
                with patch("mcp_jira.simple_mcp_server.server") as mock_server:
                    mock_server.run = AsyncMock()
                    mock_server.create_initialization_options = Mock(return_value={})
                    
                    # Run main
                    await main()
                    
                    # Verify server ran
                    mock_server.run.assert_awaited_once()
                    
                    # Verify cleanup happened (client closed)
                    mock_client_instance.close.assert_awaited_once()

