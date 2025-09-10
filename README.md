# MCP Jira Integration

A simple Model Context Protocol (MCP) server for Jira that allows LLMs to act as project managers and personal assistants for teams using Jira.

## Features

### Core MCP Tools
- **create_issue** - Create new Jira issues with proper formatting
- **search_issues** - Search issues using JQL with smart formatting
- **get_sprint_status** - Get comprehensive sprint progress reports
- **get_team_workload** - Analyze team member workloads and capacity
- **generate_standup_report** - Generate daily standup reports automatically

### Project Management Capabilities
- Sprint progress tracking with visual indicators
- Team workload analysis and capacity planning
- Automated daily standup report generation
- Issue creation with proper prioritization
- Smart search and filtering of issues

## Requirements

- Python 3.8 or higher
- Jira account with API token
- MCP-compatible client (like Claude Desktop)

## Quick Setup

1. **Clone and install**:
```bash
cd mcp-jira
pip install -e .
```

2. **Configure Jira credentials** in `.env`:
```env
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your.email@domain.com
JIRA_API_TOKEN=your_api_token
PROJECT_KEY=PROJ
DEFAULT_BOARD_ID=123
```

3. **Run the MCP server**:
```bash
python -m mcp_jira.simple_mcp_server
```

## Usage Examples

### Creating Issues
"Create a high priority bug for the login system not working properly"
- Auto-assigns proper issue type, priority, and formatting

### Sprint Management
"What's our current sprint status?"
- Gets comprehensive progress report with metrics and visual indicators

### Team Management
"Show me the team workload for john.doe, jane.smith, mike.wilson"
- Analyzes capacity and provides workload distribution

### Daily Standups
"Generate today's standup report"
- Creates formatted report with completed, in-progress, and blocked items

## MCP Integration

### With Claude Desktop
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mcp-jira": {
      "command": "python",
      "args": ["-m", "mcp_jira.simple_mcp_server"],
      "cwd": "/path/to/mcp-jira"
    }
  }
}
```

### With Other MCP Clients
The server follows the standard MCP protocol and works with any MCP-compatible client.

## Configuration

### Required Environment Variables
- `JIRA_URL` - Your Jira instance URL
- `JIRA_USERNAME` - Your Jira username/email
- `JIRA_API_TOKEN` - Your Jira API token
- `PROJECT_KEY` - Default project key for operations

### Optional Settings
- `DEFAULT_BOARD_ID` - Default board for sprint operations
- `DEBUG_MODE` - Enable debug logging (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

## Getting Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a name and copy the token
4. Use your email as username and the token as password

## Architecture

This implementation prioritizes simplicity:
- **Single MCP server file** - All tools in one place
- **Standard MCP protocol** - Uses official MCP SDK
- **Rich formatting** - Provides beautiful, readable reports
- **Error handling** - Graceful handling of Jira API issues
- **Async support** - Fast and responsive operations

## Troubleshooting

### Common Issues

1. **"No active sprint found"**
   - Make sure your board has an active sprint
   - Check that `DEFAULT_BOARD_ID` is set correctly

2. **Authentication errors**
   - Verify your API token is correct
   - Check that your username is your email address

3. **Permission errors**
   - Ensure your Jira user has appropriate project permissions
   - Check that the project key exists and you have access

### Debug Mode
Set `DEBUG_MODE=true` in your `.env` file for detailed logging.

## Contributing

1. Fork the repository
2. Make your changes
3. Test with your Jira instance
4. Submit a pull request

## License

MIT License - see LICENSE file
