# JIRA MCP Assistant

A Model Context Protocol (MCP) server that enables Claude to interact with JIRA for backlog management and issue tracking. This server provides capabilities for searching the backlog, creating issues, and updating issue details.

## Features

1. **Search Backlog**
   - Search issues in the project backlog
   - Filter by search terms
   - View issue details

2. **Update Issues**
   - Change issue priority
   - Update issue status
   - Assign issues to team members

3. **Create Issues**
   - Create new issues in the backlog
   - Set priority and type
   - Add descriptions and summaries

## Prerequisites

- Node.js v18 or higher
- JIRA instance with API access
- JIRA API token

## Getting Started

1. **Installation**
```bash
# Clone the repository
git clone https://github.com/Warzuponus/mcp-jira.git
cd mcp-jira

# Install dependencies
npm install
```

2. **JIRA API Token Setup**
- Go to https://id.atlassian.com/manage-profile/security/api-tokens
- Create an API token
- Note down your:
  - JIRA instance URL
  - Email address
  - API token

3. **Claude Desktop Configuration**

Edit your Claude Desktop configuration file:
- macOS: `~/Library/Application Support/Claude Desktop/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude Desktop\claude_desktop_config.json`

Add the following configuration:
```json
{
  "mcpServers": {
    "jira": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-jira/index.js"],
      "env": {
        "JIRA_INSTANCE_URL": "https://your-instance.atlassian.net",
        "JIRA_USER_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

4. **Restart Claude Desktop**

## Example Usage

Once configured, you can ask Claude questions like:

- "Show me all high priority items in the PROJECT backlog"
- "Create a new bug report in PROJECT for the login page crash"
- "Assign PROJ-123 to john.doe and set it to high priority"
- "What issues are currently in the PROJECT backlog?"

## Development

### Running Locally
```bash
# Set environment variables
export JIRA_INSTANCE_URL="https://your-instance.atlassian.net"
export JIRA_USER_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"

# Run the server
node index.js
```

### Testing
Test specific operations:
```bash
# Search backlog
curl -X POST http://localhost:3000/tools/search_backlog -d '{"projectKey": "PROJ"...}'

# Update issue
curl -X POST http://localhost:3000/tools/update_issue -d '{"issueKey": "PROJ-123"...}'
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
