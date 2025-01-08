# MCP Jira Integration

A Model Context Protocol (MCP) integration for Jira that enables AI assistants like Claude to interact with Jira's API. This implementation provides a standardized way to create and manage Jira issues, track sprints, and access Jira data through the MCP protocol.

## Features

### Core Functionality
- Jira issue creation and management through MCP protocol
- API key-based authentication
- Standardized request/response format for AI interactions

### Jira Integration Features
- Issue creation and updates
- Basic sprint tracking
- Project and board management
- Issue search and retrieval

## Requirements

- Python 3.8 or higher
- Jira account with API token
- Valid MCP implementation

## Setup

1. Clone the repository
2. Configure environment variables in `.env`:
   ```env
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your.email@domain.com
   JIRA_API_TOKEN=your_api_token
   PROJECT_KEY=PROJ
   API_KEY=your_secure_api_key  # For MCP authentication
   ```

## API Usage

### Create Issue
```python
from mcp_jira.protocol import MCPRequest, MCPContext

# Create request context
context = MCPContext(
    conversation_id=\"conv-123\",
    user_id=\"user-123\",
    api_key=\"your_api_key\"
)

# Create issue request
request = MCPRequest(
    function=\"create_issue\",
    parameters={
        \"summary\": \"Implement feature X\",
        \"description\": \"Detailed description\",
        \"issue_type\": \"Story\",
        \"priority\": \"High\"
    },
    context=context
)

response = await mcp_handler.process_request(request)
```

### Search Issues
```python
request = MCPRequest(
    function=\"search_issues\",
    parameters={
        \"jql\": \"project = PROJ AND status = 'In Progress'\"
    },
    context=context
)

response = await mcp_handler.process_request(request)
```

## Authentication

All requests require an API key in the request header:
```python
headers = {
    \"X-API-Key\": \"your_api_key\"
}
```

## Integration with AI Assistants

This MCP implementation is designed to work with AI assistants that support the MCP protocol:

1. Configure the environment variables
2. Set up the MCP endpoint in your AI assistant's configuration
3. Use the standardized MCP protocol for Jira interactions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file`,
  `message`: `Update README to reflect current functionality`
}
