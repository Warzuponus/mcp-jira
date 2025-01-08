# MCP Jira with Scrum Master Features

A Python-based Model Context Protocol (MCP) server for Jira that includes enhanced Scrum Master and Executive Assistant capabilities. This MCP implementation allows Claude to interact with Jira, manage sprints, and provide Scrum Master assistance.

## Features

### Core MCP Features
- Jira issue creation and management
- Sprint tracking and metrics
- Resource and function-based MCP protocol
- API key authentication

### Scrum Master Features
- Automated sprint planning
- Progress analysis and tracking
- Workload balancing
- Risk identification
- Priority management

### Executive Assistant Features
- Daily standup report generation
- Sprint metrics and analytics
- Team performance tracking
- Blocking issue detection

## Requirements

- Python 3.8 or higher
- Jira account with API token
- FastAPI
- Pydantic
- aiohttp

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Configure environment variables in `.env`:
   ```env
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your.email@domain.com
   JIRA_API_TOKEN=your_api_token
   PROJECT_KEY=PROJ
   DEFAULT_BOARD_ID=123
   API_KEY=your_secure_api_key  # For MCP authentication
   ```

## Usage

1. Start the server:
   ```bash
   uvicorn mcp_jira.server:app --reload
   ```

2. Access the API documentation at `http://localhost:8000/docs`

## API Examples

### Create Issue
```python
# First, initialize the components
from mcp_jira.mcp_protocol import MCPProtocolHandler, MCPRequest, MCPContext, MCPResourceType
from mcp_jira.types import IssueType, Priority

# Create request context
context = MCPContext(
    conversation_id="test-conv",
    user_id="test-user",
    api_key="your_api_key"
)

# Create and send request
request = MCPRequest(
    function="create_issue",
    parameters={
        "summary": "Implement feature X",
        "description": "Detailed description",
        "issue_type": "Story",
        "priority": "High",
        "story_points": 5
    },
    context=context,
    resource_type=MCPResourceType.ISSUE
)

response = await mcp_handler.process_request(request)
```

### Plan Sprint
```python
request = MCPRequest(
    function="plan_sprint",
    parameters={
        "sprint_id": 123,
        "target_velocity": 30,
        "team_members": ["user1", "user2"]
    },
    context=context,
    resource_type=MCPResourceType.SPRINT
)

response = await mcp_handler.process_request(request)
```

### Analyze Progress
```python
request = MCPRequest(
    function="analyze_sprint",
    parameters={
        "sprint_id": 123
    },
    context=context,
    resource_type=MCPResourceType.SPRINT
)

response = await mcp_handler.process_request(request)
```

## Authentication

All API requests require an API key to be provided in the request header:
```python
headers = {
    "X-API-Key": "your_api_key"
}
```

## Claude Desktop Integration

To use this MCP with Claude Desktop:

1. Install the package
2. Set up your environment variables
3. Use the provided example scripts in the `examples` directory

Example:
```python
from mcp_jira.examples.claude_test import handle_claude_request

# Test with Claude
message = "Create a new issue for implementing user authentication"
response = await handle_claude_request(message)
print(response)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file